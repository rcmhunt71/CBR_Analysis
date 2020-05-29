import argparse
import re
import time
import typing
import unicodedata

import jira
import xlsxwriter
from xlsxwriter.worksheet import Worksheet


class CommandLineOptions:
    """ The utility command line arguments. """

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('user', help="Username (for Jira Access)")
        self.parser.add_argument('pswd', help="Password (for Jira Access)")
        self.parser.add_argument('start', help="Start of date range for query. Format: CCYY-MM-DD")
        self.parser.add_argument('stop', help="Stop of date range for query. Format: CCYY-MM-DD")
        self.parser.add_argument('-m', '--max_results', default=DEFAULT_MAX_RESULTS,
                                 help=f"Max number of records to return. Default: {DEFAULT_MAX_RESULTS}")
        self.parser.add_argument('-d', '--debug', action='store_true', default=False,
                                 help="Enable debugging. Default: False")

        self.args = self.parser.parse_args()

    def get_args(self):
        return self.args


class MDExceptions:
    """
    These are the various Mortgage Director exceptions (these have been seen, but there could be additional
    exceptions which should be added here.

    The "GENERAL_EXCEPTION_PATTERN" removes the server information and matches the remainder of the msg for
    additional parsing.

    * <EXCEPTION>s are based on the exception type listed in the defect summary (title). The corresponding parsing
    patterns are stored as a list: <EXCEPTION>_PARSE.

    * The various <EXCEPTION>_PARSE elements are lists of regular expression patterns, matching the various
    messages that have been seen with the exception.

    """

    # For consistency, this is the name of the "named pattern" to extract user-added data from the description.
    # It is defined here so external classes can reference the "extra data" without worrying if the named_group name
    # changes later.
    EXTRA = 'extra'

    # All exception messages have the server name. This pattern removes the server name and returns the remainder of
    # the message.
    GENERAL_EXCEPTION_PATTERN = re.compile(
        r'server hostname:.*?[\r\n]+(?P<error_msg>.*)',
        re.IGNORECASE | re.DOTALL)

    # ----------------------------------------------------------------------------------------
    # <EXCEPTION_NAME>_PARSE regular expression pattern lists - stored in alphabetical order.
    # ----------------------------------------------------------------------------------------
    EACCESSVIOLATION_PARSE = [
        re.compile(
            r'address\s+(?P<violation_address>[\w\d]+)\.?\s*'
            r'(in module\s*\'[\w\d.]+\'\.)?'
            r'\s*.* of address\s*(?P<address>[\d\w]+)\.(?P<extra>.*)?',
            re.IGNORECASE | re.DOTALL),
    ]

    EARGUMENTOUTOFRANGEEXCEPTION_PARSE = GENERAL_EXCEPTION_PATTERN
    ECONVERTERROR_PARSE = GENERAL_EXCEPTION_PATTERN
    EDIRECTORYNOTFOUNDEXCEPTION_PARSE = GENERAL_EXCEPTION_PATTERN

    EDATABASEERROR_PARSE = [
        re.compile(r'\'(?P<value>.*)\'\s+is not a valid .* value .*\'\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),
        re.compile(r'((?P<form>.*): )?cannot modify a read-only dataset\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),
        re.compile(r'Bookmark not found (?P<bookmark>.*)', re.IGNORECASE | re.DOTALL),
    ]

    EEXTERNALEXCEPTION_PARSE = [
        re.compile(r'address\s+(?P<violation_address>[\w\d]+).*'
                   r'address\s+(?P<read_address>[\w\d]+).*'
                   r'address:\s+(?P<v_address>[\w\d]+)\s+\((?P<r_address>[\w\d]+)\)\.'
                   r'(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),
    ]

    EFCREATEERROR_PARSE = GENERAL_EXCEPTION_PATTERN
    EFOPENERROR_PARSE = GENERAL_EXCEPTION_PATTERN

    EIHMCUSTOMEXCEPTION_PARSE = [
        re.compile(
            r'.*'
            r'^thread id =(?P<thread_id>\d+).*'
            r'^.*dataset name = [\w\d]+$'
            r'.*'
            r'^cannot.*\]\.'
            r'(?P<extra>.*)?',
            re.IGNORECASE | re.MULTILINE | re.DOTALL),

        re.compile(
            r'thread id\s*=\s*(?P<thread_id>\d+)[\r\n]*'
            r'dataset name = [\w\d]+[\r\n]+\s*'
            r'.*after login:.*\.(?P<extra>.*)?',
            re.IGNORECASE | re.DOTALL),

        re.compile(
            r'thread id\s*=\s*(?P<thread_id>\d+)[\r\n]*'
            r'dataset name = [\w\d]+[\r\n]+\s*'
            r'invariant operation\.(?P<extra>.*)?',
            re.IGNORECASE | re.DOTALL),
    ]

    EINOUTERROR_PARSE = [
        re.compile(r'create file\s+"(?P<filename>[\w\d.\\:]+)"\..*process.(?P<extra>.*)?'),
    ]

    EINTOVERFLOW_PARSE = GENERAL_EXCEPTION_PATTERN
    EINVALIDCAST_PARSE = GENERAL_EXCEPTION_PATTERN

    EINVALIDOPERATION_PARSE = [
        re.compile(r'no parent window\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),
        re.compile(r'disabled or invisible window\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),
    ]

    EJCLANSISTRINGLISTERROR_PARSE = [
        re.compile(r'index out of bounds\s*\((?P<index>\d+)\)\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),
    ]

    ELISTERROR_PARSE = [
        re.compile(r'index out of bounds\s*\((?P<index>\d+)\)\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),
    ]

    EOLEEXCEPTION_PARSE = GENERAL_EXCEPTION_PATTERN
    EOLESYSERROR_PARSE = GENERAL_EXCEPTION_PATTERN
    EVARIANTINVALIDOPERROR_PARSE = GENERAL_EXCEPTION_PATTERN

    EXCEPTION_PARSE = [
        re.compile(r'at address\s+(?P<v_address>[\w\d]+)\s+.*'
                   r'of address\s+(?P<r_address>[\w\d]+)\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),

        re.compile(r'.*?[\r\n]+(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),
    ]


# Directive to avoid typing issues with Jira objects
# noinspection PyUnresolvedReferences
class DefectInfo:
    """
    This class defines:
       * the structure to store each defect (defect id, type of error, version/build number)
       * parses the summary (title) and description for relevant data.
    """

    # Parses the summary (title) for the error number, bug_id, version
    SUMMARY_PARSE = re.compile(
        r'(?P<error>\w+)\s+'
        r'\(.*\s+(?P<bug_id>[\w\d]+);'
        r'\s+v(?P<version>[\d.]+)\)',
        re.IGNORECASE)

    def __init__(self, jira_issue: jira.Issue, debug: bool = False) -> typing.NoReturn:
        """
        Initialize the object and parse the relevant data/fields.

        Args:
            jira_issue: Single Jira Issue (as defined by the jira package)
            debug: Enable debug messages

        """
        self.jira = jira_issue
        self._debug = debug
        self.exception_type, self.bug_id, self.version = self._parse_summary()
        self.error_msg = None
        self.general_error_msg = None
        self.user_added_data = None
        self._parse_metadata()

    @property
    def defect_id(self) -> str:
        """
        Returns: (str) - Defect ID
        """
        return self.jira.key

    @property
    def title(self) -> str:
        """
        Returns: (str) - Defect title
        """
        return self.jira.fields.summary

    def __str__(self) -> str:
        """
        Returns: string representation of the DefectInfo obj
        """

        # Find all properties that are not capitalized or prefixed with an underscore. These will be
        # the class attributes that contain the defect data.
        obj_attrs = [x for x in dir(self) if not x.startswith('_') and x[0].upper() != x[0]]

        output = f"{self.defect_id}:\n"
        for attr in sorted(obj_attrs):
            output += f"\t{attr.upper()}: {getattr(self, attr)}\n"
        return output

    def _parse_summary(self) -> typing.Tuple[str, str, str]:
        """
        Parse the issue summary (title) for error id, defect id, and version/build number.

        Returns: Tuple(error_id, bug_id, version/build number)

        """
        match = self.SUMMARY_PARSE.match(self.jira.fields.summary)
        if match is not None:
            return match.group('error'), match.group('bug_id'), match.group('version')
        return '', '', ''

    def _parse_general_exception_msg(self) -> typing.NoReturn:
        """
        Parse the description to remove the server name and save the remainder of the text.

        Returns: None

        """
        pattern = MDExceptions.GENERAL_EXCEPTION_PATTERN
        message = self._remove_control_characters(self.jira.fields.description)
        match = pattern.search(message)

        if match is not None:
            for attr, value in match.groupdict().items():
                setattr(self, attr, value)
        else:
            # 'match is None' indicates that the full (raw) description does not match the general expected format.
            # Save the message, but no additional processing will be done.
            if self._debug:
                print(f"NOTE: Unable to match {pattern} to:\n'{message}'")
            self.general_error_msg = message

    def _parse_metadata(self) -> typing.NoReturn:
        """
        Parse the description to genericize the field for matching common errors/failures.

        Returns: None

        """
        # Remove the server name from the raw message
        # Stores in self.<general exception group name> --> e.g - self.error_msg
        self._parse_general_exception_msg()

        # Determine the correct exception parsing list
        pattern_name = f"{self.exception_type.upper()}_PARSE"
        try:
            patterns = getattr(MDExceptions, pattern_name)
        except AttributeError:
            print(f"ERROR: Unable to find EXCEPTION pattern: {pattern_name}")
            return
        else:
            # Pattern found, but not specific patterns defined, so the entire message will be stored.
            if not isinstance(patterns, list):
                return

        # Iterate through the pattern list to see if there is a match.
        match = None
        for pattern in patterns:
            match = pattern.search(self._remove_control_characters(self.error_msg))

            # Match found, replace error/instance specific data with <data_field_type> string and stop.
            if match is not None:
                self._substitute_matches(match)
                break

        # No match was found in the list of patterns
        if match is None and len(patterns) > 0 and self._debug:
            formatted_out_msg = ''.join([f"\t{line}\n" for line in self.error_msg.split("\n")])
            print(f"- {pattern_name}: Unable to find a generic pattern matching the description in list.")
            print(f"  Description:\n{formatted_out_msg}\n")

    def _substitute_matches(self, match: re.Match) -> typing.NoReturn:
        """
        Removes specific data matches with generic <data_found> in error message.

        Args:
            match: re.match --> regular expression match (groups)

        Returns: None

        """
        msg = self.error_msg

        # Iterate through regexp matched groups
        for data_type, str_match in match.groupdict().items():

            # If user-specific data, strip the data from the msg and store in user_added_data.
            if data_type == MDExceptions.EXTRA:
                if str_match is not None and str_match != '':
                    msg = re.sub(str_match, '', msg)
                    self.user_added_data = str_match

            # If the match is not "None" - for optional match arguments e.g. - (?P<example>.*)?
            # Try to replace the data with a generic '<group_name>' element.
            elif str_match is not None:
                data_type = data_type.split('_')[-1]
                try:
                    msg = re.sub(str_match, f'<{data_type}>', msg)
                except re.error:
                    if self._debug:
                        print(f"Unable to substitute '{str_match}' to '<{data_type}>'")

        # Replace the <CR>s (\n or \r\n) with single '\n' and store
        self.general_error_msg = re.sub(re.compile(r'[\r\n]+'), r'\n', msg)

    @classmethod
    def _remove_control_characters(cls, string: str) -> str:
        """
        Remove any non-printing control characters

        Args:
            string: text to process

        Returns:
            A string with all non-printing control characters removed.

        """
        return "".join(character for character in string if unicodedata.category(character).lower() != "cf")


class Defects(list):
    """
    Class creates a list of DefectInfo objects, provides methods for tallying and generating report structures.
    """
    def __init__(self, issue_list: typing.List[jira.Issue], debug: bool = False) -> typing.NoReturn:
        """
        Instantiate the Defects List object
        Args:
            issue_list: List of Jira Issues (jira.issue from jira package).
            debug: Enable debug messaging output. (Default: False)

        """
        super().__init__()
        self.debug = debug
        self.extend([DefectInfo(defect, debug=self.debug) for defect in issue_list])

    @property
    def exception_types(self) -> typing.List[str]:
        """
        Aggregate a unique list of all types of exceptions within the defect list.

        Returns:
            List of types of exceptions

        """
        return list(set([defect_info_obj.exception_type for defect_info_obj in self]))

    def tally_defect_types(self) -> typing.Dict[str, int]:
        """
        Build a dictionary of all exception types and their counts.

        Returns:
            A dictionary (k,v) => <exception_type>: <count of defects of the exception type>

        """
        # Initialize dictionary with all exception types.
        issue_type_tally = dict([(issue_type, 0) for issue_type in self.exception_types])

        # Generate the tally per exception type
        for defect_info_obj in self:
            issue_type_tally[defect_info_obj.exception_type] += 1

        return issue_type_tally

    def defects_ids_based_on_exception_type(self, use_defect_obj: bool = False) -> typing.Dict[str, typing.List[str]]:
        """
        Build a dictionary of all exception type and the defect id
        Args:
            use_defect_obj: Rather than store the defect id, store the jira.issue.

        Returns:
            A dictionary (k,v) => <exception_type>: <List of defects ids having the exception type>

        """
        # Initialize the dictionary with all exception types
        defect_dict = dict([(x, []) for x in self.exception_types])

        # Generate the list of defects per exception type
        for defect in self:
            data = defect if use_defect_obj else defect.defect_id
            defect_dict[defect.exception_type].append(data)

        return defect_dict

    def build_reporting_dict(self) -> typing.Dict[str, dict]:
        """
        Builds detailed dictionary of data per exception type (such as SW ver/build, defect IDs, generic summary)

        Returns:
            A dictionary of detailed info:
                <exception>:
                  <summary>:
                     <version>:
                        - list of defect ids for the given error msg.

        """
        # Initialize the dictionary with all exception types
        defect_dict = dict([(x, {}) for x in self.exception_types])

        for defect in self:
            if hasattr(defect, 'error_msg'):

                # Determine the generic error msg (if not parsed, get the general_error_msg)
                error_msg = defect.error_msg if defect.general_error_msg is None else defect.general_error_msg

                # Check if the current msg has been encountered before
                # if not, add it to the dictionary with a child dict.
                if error_msg not in defect_dict[defect.exception_type].keys():
                    defect_dict[defect.exception_type][error_msg] = {}

                # Check if the current msg has been encountered before
                # if not, add it to the dictionary with a child dict.
                if defect.version not in defect_dict[defect.exception_type][error_msg].keys():
                    defect_dict[defect.exception_type][error_msg][defect.version] = []

                # Make note if the defect has additional user data; add defects to list
                extra_data = '' if defect.user_added_data is None else '*'
                defect_dict[defect.exception_type][error_msg][defect.version].append(f'{defect.defect_id}{extra_data}')

        return defect_dict


class ExcelWorkbook:
    """
    The class builds an XLSX spreadsheet with summary and detailed defect info, using the Defects class method output.
    """

    EXTENSION = 'xlsx'

    def __init__(self, workbook_name: str) -> typing.NoReturn:
        """
        Initialize the workbook and define the basic formats that will be used in the worksheets/cells.
        Args:
            workbook_name: Name of XLSX workbook (which will be used as the filename). The extension 'xlsx' will
                be appended to the filename if it is not present.

        """
        self.wkbk_name = (workbook_name if workbook_name.lower().endswith(self.EXTENSION) else
                          f'{workbook_name}.{self.EXTENSION}')
        self.workbook = xlsxwriter.Workbook(self.wkbk_name)
        self._define_cell_formats()

    def _define_cell_formats(self) -> typing.NoReturn:
        """
        Defines the various formats used in the worksheets.

        Returns:
            None

        """
        self.bold = self.workbook.add_format({'bold': True})

        # Header cells: Grey background, bold text
        self.header_cell = self.workbook.add_format({'bold': True})
        self.header_cell.set_bg_color('#d4d4d4')

        # Colorize the entire row (light grey), bold all cell text.
        self.grey_row = self.workbook.add_format({'bold': True})
        self.grey_row.set_bg_color('#c4c4c4')

    @staticmethod
    def freeze_header_row(worksheet: Worksheet) -> typing.NoReturn:
        """
        Freezes the first row (row 0).
        Args:
            worksheet: Worksheet to freeze header

        Returns:
            None

        """
        worksheet.freeze_panes(1, 0)

    def build_summary_sheet(self, data_dict: typing.Dict[str, int], name: str = 'Summary') -> typing.NoReturn:
        """
        Build the summary sheet: a list of all exceptions and their relative defect/issue counts.

        Args:
            data_dict: Dictionary from Defects.tally_defect_types()
            name: Name of worksheet (Default: Summary)

        Returns:
            None

        """
        exception_header = 'Exception'
        total_count_header = 'Total Count'
        total_header = 'Total'

        # Determine which row the data summary will be located and how many rows to total.
        total_row_num = len(data_dict.keys()) + 1
        total_sum_formula = f"=SUM(B1:B{total_row_num})"

        wksht = self.workbook.add_worksheet(name=name)

        # Define the table header and track the size of the various entries per column
        wksht.write(0, 0, exception_header, self.header_cell)
        wksht.write(0, 1, total_count_header, self.header_cell)
        max_widths = self._find_max_col_widths(col_entries=[exception_header, total_count_header])

        # Add exceptions and counts (per row). Data sorted by counts, in descending order
        for row, (exc, issue_count) in enumerate(sorted(data_dict.items(), key=lambda x: x[1], reverse=True), 1):
            wksht.write_string(row, 0, exc)
            wksht.write_number(row, 1, issue_count)
            max_widths = self._find_max_col_widths(col_entries=[exc, issue_count], widths=max_widths)

        # Add the summary row
        wksht.write(total_row_num, 0, total_header, self.header_cell)
        wksht.write(total_row_num, 1, total_sum_formula, self.header_cell)
        max_widths = self._find_max_col_widths(col_entries=[total_header, 'SUM'], widths=max_widths)

        # Adjust columns to width of widest entry in column. Freeze the header row.
        self._set_column_widths(wksht, max_widths)
        self.freeze_header_row(worksheet=wksht)

    def build_detailed_table(self, data_dict: typing.Dict[str, dict], name: str = 'Details') -> typing.NoReturn:
        """
        Build a detailed report worksheet of the issues.

        Args:
            data_dict: Dictionary - DefectList.build_reporting_dict()
            name: Name of worksheet (default: Details)

        Returns:
            None
        """

        # Column header values
        exception_header = 'Exception'
        version_header = 'Version'
        summary_header = 'Summary'
        defect_ids_header = 'Defect IDs'
        defect_count_header = 'Defect Count'

        # For some columns, the entries can be very long (e.g. - descriptions), so an override is specified.
        # If the maximum entry length of a given column exceeds the override value,
        # set the corresponding maximum to the override value. (-1 means no override set).
        # NOTE: if the column order is changed, please refer to the debugging note lower in this routine.
        defect_list_column_width = 100
        column_info = {
            exception_header: -1,
            summary_header: 150,
            defect_count_header: -1,
            version_header: -1,
            defect_ids_header: defect_list_column_width,
        }

        wksht = self.workbook.add_worksheet(name=name)

        # Determine the column names and the corresponding width overrides.
        columns = list(column_info.keys())
        max_width_overrides = list(column_info.values())

        max_widths = self._find_max_col_widths(col_entries=columns, overrides=max_width_overrides)

        # Define headers
        for col_index, col_name in enumerate(columns, 0):
            wksht.set_row(0, None, self.bold)
            wksht.write_string(0, col_index, col_name)

        # For each exception... (sorted based on number of defects, in descending order)
        row_index = 1
        for exc_name, exc_dict in sorted(
                data_dict.items(),
                key=lambda x: sum([len(def_ids) for defect in x[1].keys()
                                   for ver in x[1][defect].keys()
                                   for def_ids in x[1][defect][ver]]),
                reverse=True):

            # Save the exception parent row - used to add sum of issues associated with exception to the same row.
            parent_exc_row = row_index
            total_exc_defect_counts = 0

            # Record exception
            wksht.set_row(row_index, None, self.grey_row)
            wksht.write_string(row_index, columns.index(exception_header), exc_name)
            row_index += 1

            # Add Summary (generalized description)
            for summary, exc_details_dict in sorted(
                    exc_dict.items(), key=lambda x: sum([len(x[1][ver]) for ver in x[1].keys()]), reverse=True):
                wksht.write_string(row_index, columns.index(summary_header), summary)

                # Add version, Defect ID, and Defect Count data; sorted by version
                # Each unique version will be put on a separate row
                for version, defect_ids_list in sorted(exc_details_dict.items(), key=lambda x: len(x[0]), reverse=True):
                    wksht.write_string(row_index, columns.index(version_header), version)
                    wksht.write_string(row_index, columns.index(defect_ids_header), ", ".join(defect_ids_list))
                    wksht.write_number(row_index, columns.index(defect_count_header), len(defect_ids_list))
                    total_exc_defect_counts += len(defect_ids_list)

                    # =========================================================================================
                    # DEBUGGING NOTE
                    # =========================================================================================
                    # If the column widths are off... check that the parameter list (below) is in the correct
                    # order as defined in the column_info dictionary at the top of this routine.
                    # If the column order is changed, the list in this call needs to be updated to match.
                    # =========================================================================================
                    max_widths = self._find_max_col_widths(
                        [exc_name, summary, str(len(defect_ids_list)), version, "-" * defect_list_column_width],
                        widths=max_widths, overrides=max_width_overrides)
                    row_index += 1

            # Add the total issue count for the exception to the same row as the exception entry.
            wksht.write_number(parent_exc_row, columns.index(defect_count_header), total_exc_defect_counts)
            row_index += 1

        # Add a note about the <defect_id>* notation
        wksht.write_string(row_index, columns.index(summary_header),
                           "NOTE: '*' next to the defect id indicates additional user input found in the description.",
                           self.bold)

        # Adjust the columns based on the widest entry per column; freeze the header row.
        self._set_column_widths(wksht, max_widths)
        self.freeze_header_row(worksheet=wksht)

    @staticmethod
    def _find_max_col_widths(
            col_entries: typing.List[typing.Any], widths: typing.List[int] = None,
            overrides: typing.List[int] = None) -> typing.List[int]:
        """
        Determines the longest entry (character width) per column, as data is added to each row.

        Args:
            col_entries: list of data to each column for a give row.
            widths: list of currently longest character length entry found for each column.
            overrides: list of maximum widths allowed for each column.

        Returns:
            List of max width (characters) per column.

        """

        # If no list of widths is provided, create a list initialized to 0 for each column.
        if widths is None:
            widths = [0 for _ in col_entries]

        # If no list of overrides is provided, create a list initialized to 0 for each column.
        if overrides is None:
            overrides = [0 for _ in col_entries]

        # Accumulate the max value for each column for the current row.
        max_widths = [max([len(str(value)), widths[index]]) for index, value in enumerate(col_entries, 0)]

        # Check each max value and adjust if greater than corresponding override value.
        for index, max_width in enumerate(max_widths, 0):
            if 0 < overrides[index] < max_width:
                max_widths[index] = overrides[index]
        return max_widths

    @staticmethod
    def _set_column_widths(
            worksheet: Worksheet, col_widths: typing.List[int], column_buffer: int = 0) -> typing.NoReturn:
        """
        Sets the width of each column to the specifed width
        Args:
            worksheet: XlsxWriter worksheet to adjust
            col_widths: List of widths
            column_buffer: Optional: add small increment to max value for each column

        Returns:
            None

        """
        for index, col_width in enumerate(col_widths, 0):
            worksheet.set_column(index, index, col_width + column_buffer)

    def save(self) -> typing.NoReturn:
        """
        Close the workbook and save file. Can only be called ONCE on a workbook; cannot save multiple times.

        Returns:
            None

        """
        self.workbook.close()
        print(f"- Wrote XLSX file to: '{self.wkbk_name}'")


def get_jira_issues(
        client: jira.JIRA, project: str, query: str, max_results: int,
        start_date: str, stop_date: str) -> typing.List[jira.Issue]:
    """
    Query the specified JIRA Project for issues that match JQL query. The routine will measure the time required
    to gather the data, so the processing performance can be monitored and improved as needed.

    Args:
        client: Instantiated Jira Client
        project: Target Jira project
        query: JQL query
        max_results: Maximum number of results to return.
        start_date: Start date of query (CCYY-MM-DD formatted string)
        stop_date: Stop date of query (CCYY-MM-DD formatted string)

    Returns:
        List of Jira Issues (jira.Issue)

    """
    print(f"- Querying JIRA '{project}' project for all issues in 'To Do' in range of '{start_date}' to '{stop_date}'.",
          end='', flush=True)
    start_time = time.perf_counter()
    results = client.search_issues(jql_str=query, maxResults=max_results)
    print(f" --> Complete. {len(results)} found. ({time.perf_counter() - start_time:0.2f} secs)")
    return results


def connect_to_jira(url: str, user: str, password: str) -> jira.JIRA:
    """
    Connects to Jira; tracks timing to connect.

    Args:
        url: URL to connect to JIRA
        user: Username
        password: Password

    Returns:
        Instantiated JIRA Client

    """
    print(f"- Connecting to Jira... ", end='', flush=True)
    start_time = time.perf_counter()
    client = jira.JIRA(url, basic_auth=(user, password))
    print(f"Connected. ({time.perf_counter() - start_time:0.2f} secs)")
    return client


if __name__ == '__main__':

    # Default values for accessing JIRA
    DEFAULT_MAX_RESULTS = 500
    PROJECT = 'CBR'
    STATUS = ['"To Do"']
    URL = 'https://jira.pclender.com'

    # Get the CLI arguments
    cli = CommandLineOptions()
    args = cli.get_args()

    # Build the JQL query.
    JQL = (f'project = {PROJECT} '
           f'AND status in ({",".join(STATUS)}) '
           f'AND created >= {args.start} '
           f'AND created <= {args.stop} '
           f'ORDER BY priority DESC, updated DESC')

    # Connect to Jira and query defects matching criteria
    jira_client = connect_to_jira(url=URL, user=args.user, password=args.pswd)
    jira_issues = get_jira_issues(client=jira_client, project=PROJECT, query=JQL, max_results=args.max_results,
                                  start_date=args.start, stop_date=args.stop)

    # Process and categorize the list of Jira defects
    start_processing = time.perf_counter()
    issues = Defects(jira_issues)
    print(f"- Parsing of returned defects complete. ({time.perf_counter() - start_processing:0.2f} secs)")

    # Record results to Excel spreadsheet.
    start_processing = time.perf_counter()
    xlsx_name = f"{PROJECT}_issues_{args.start}_to_{args.stop}.{ExcelWorkbook.EXTENSION}"
    xlsx = ExcelWorkbook(workbook_name=xlsx_name)
    xlsx.build_summary_sheet(issues.tally_defect_types())
    xlsx.build_detailed_table(issues.build_reporting_dict())
    xlsx.save()
    print(f"- XLSX processing complete. ({time.perf_counter() - start_processing:0.2f} secs)")

    # Display summary of the exceptions and corresponding issue counts.
    total_count = 0
    for exc_type, count in sorted(issues.tally_defect_types().items(), key=lambda x: x[1], reverse=True):
        print(f"- '{exc_type}': {count}")
        total_count += count
    print(f"Total Issue Count: {total_count}")

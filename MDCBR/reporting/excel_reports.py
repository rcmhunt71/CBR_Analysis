import logging
import typing

import xlsxwriter
from xlsxwriter.worksheet import Worksheet


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
        self.log = logging.getLogger(self.__class__.__name__)

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

    def _find_max_col_widths(
            self, col_entries: typing.List[typing.Any], widths: typing.List[int] = None,
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
                self.log.debug(f'Column {index} width override applied. '
                               f'Width: {max_width} Override: {overrides[index]}')
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
        status = f"- Wrote XLSX file to: '{self.wkbk_name}'"
        self.log.info(status)
        print(status)

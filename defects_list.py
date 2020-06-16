import logging
import typing

from defect_info import DefectInfo

import jira


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
        self.log = logging.getLogger(self.__class__.__name__)
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

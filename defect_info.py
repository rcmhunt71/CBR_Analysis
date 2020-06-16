import logging
import re
import typing
import unicodedata

import elf_parser
from md_exceptions import MDExceptions

import jira


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

    ELF_LOG_EXTENSION = 'el'

    def __init__(self, jira_issue: jira.Issue, debug: bool = False) -> typing.NoReturn:
        """
        Initialize the object and parse the relevant data/fields.

        Args:
            jira_issue: Single Jira Issue (as defined by the jira package)
            debug: Enable debug messages

        """
        self.jira = jira_issue
        self._debug = debug
        self.log = logging.getLogger(self.__class__.__name__)
        self.error_msg = None
        self.general_error_msg = None
        self.user_added_data = None

        self.exception_type, self.bug_id, self.version = self._parse_summary()
        self._parse_metadata()
        self._elf_contents_obj = elf_parser.ELFLogParser(binary_content=self._get_elf_attachment())

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

    @property
    def elf_log_model(self) -> elf_parser.ELFLogParser:
        return self._elf_contents_obj

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
        match = self.SUMMARY_PARSE.match(self.title)
        if match is not None:
            results = match.group('error'), match.group('bug_id'), match.group('version')
            self.log.debug(f"{self.defect_id}: Parsed summary: {results}")
            return results
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
                self.log.debug(f'{self.defect_id}:    - Added attribute: "{attr}" -> "{value}"')
        else:
            # 'match is None' indicates that the full (raw) description does not match the general expected format.
            # Save the message, but no additional processing will be done.
            self.log.debug(f"{self.defect_id} --> NOTE: Unable to match {pattern} to:'{message}'.")
            self.log.debug(f"{self.defect_id} -->       Saving message to general_error_msg.")

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
        self.log.debug(f"{self.defect_id}: Using pattern: '{pattern_name}'")
        try:
            patterns = getattr(MDExceptions, pattern_name)
        except AttributeError:
            self.log.error(f"{self.defect_id}: Unable to find EXCEPTION pattern: {pattern_name}")
            return
        else:
            # Pattern found, but not specific patterns defined, so the entire message will be stored.
            if not isinstance(patterns, list):
                self.log.debug(f"{self.defect_id}: '{pattern_name}' is not a list. No additional parsing required.")
                return

        # Iterate through the pattern list to see if there is a match.
        match = None
        for index, pattern in enumerate(patterns, 0):
            match = pattern.search(self._remove_control_characters(self.error_msg))

            # Match found, replace error/instance specific data with <data_field_type> string and stop.
            if match is not None:
                self.log.debug(f"{self.defect_id}: Match found for msg. Pattern number: {index}")
                self._substitute_matches(match)
                break

        # No match was found in the list of patterns
        if match is None and len(patterns) > 0:
            formatted_out_msg = [f"\t{line}" for line in self.error_msg.split("\n")]
            spacer = " " * len(self.defect_id)
            self.log.warning(f"{self.defect_id} - {pattern_name}: "
                             f"Unable to find a generic pattern matching the description in list.")
            self.log.warning(f"{self.defect_id}   Description:")
            for line in formatted_out_msg:
                self.log.info(f"{spacer}   - {line}")

    def _substitute_matches(self, match: re.Match) -> typing.NoReturn:
        """
        Removes specific data matches with generic <data_found> in error message.

        Args:
            match: re.match --> regular expression match (groups)

        Returns: None

        """
        mesg = self.error_msg

        # Iterate through regexp matched groups
        for data_type, str_match in match.groupdict().items():

            # If user-specific data, strip the data from the msg and store in user_added_data.
            if data_type == MDExceptions.EXTRA:
                if str_match is not None and str_match != '':
                    mesg = re.sub(str_match, '', mesg)
                    self.user_added_data = str_match
                    updated_user_data = self.user_added_data.lstrip('\r\n \t')
                    self.log.debug(f'{self.defect_id}: Extra info found --> "{updated_user_data}"')

            # If the match is not "None" - for optional match arguments e.g. - (?P<example>.*)?
            # Try to replace the data with a generic '<group_name>' element.
            elif str_match is not None:
                data_type = data_type.split('_')[-1]
                try:
                    mesg = re.sub(str_match, f'<{data_type}>', mesg)
                    self.log.debug(f"{self.defect_id}: Substituted '{data_type}' for '{str_match}'.")
                except re.error:
                    self.log.debug(f"{self.defect_id}: Unable to substitute '{str_match}' to '<{data_type}>'")

        # Replace the <CR>s (\n or \r\n) with single '\n' and store
        self.general_error_msg = re.sub(re.compile(r'[\r\n]+'), r'\n', mesg).strip('\r\n \t')
        self.log.debug(f"{self.defect_id}: Final genericized msg: {self.general_error_msg}")

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

    def _get_elf_attachment(self) -> str:
        """
        Get elf file attachment name, download the attachment and return the stream as a string.

        :return: String of attachment contents.

        """
        for attachment in self.jira.fields.attachment:
            if attachment.filename.endswith(self.ELF_LOG_EXTENSION):
                return str(attachment.get())
        return ''

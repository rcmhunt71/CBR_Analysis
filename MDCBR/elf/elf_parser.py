from collections import namedtuple
import dataclasses
import re
import typing


class SectionNotFound(Exception):
    pass


class UnableToParseELFLog(Exception):
    pass


@dataclasses.dataclass
class ELFLogSections:
    """
    Common Headings and Fields found in the ELF logs.
    These values are case sensitive, and must match what is found in the logs.
    """
    APPLICATION: str = 'Application'
    EXCEPTION: str = 'Exception'
    USER: str = 'User'
    ACTIVE_CONTROLS: str = 'Active Controls'
    COMPUTER: str = 'Computer'
    OPERATING_SYSTEM: str = 'Operating System'
    NETWORK: str = 'Network'
    CALL_STACK_INFORMATION: str = 'Call Stack Information'
    MODULES: str = 'Modules Information'
    PROCESSES_INFORMATION: str = 'Processes Information'
    ASSEMBLER_INFORMATION: str = 'Assembler Information'
    REGISTERS: str = 'Registers'

    @classmethod
    def list_sections(cls) -> typing.List[str]:
        """
        Return a list of the known/defined/supported ELF log section names.

        :return:
            List of section names (strings)
        """
        return [x.name for x in dataclasses.fields(cls)]


class ELFDataTuples:
    """
    Defines the log format for each section. The class is primarily a dictionary of the sections.
    The key is the section name (as defined in ELFLogSections).
    The value is a dictionary of:
       * elements: List of elements in the section. These are lower case, all space delimiters converted to underscores.
           All headings that match a reserved object-level word in python are suffixed with an underscore. This is due
           to using a named tuples as the element data store, and named tuples have properties common to all objects,
           so any header that matches that property needs to be modified.
       * reserved_names: list of headings that match object-level reserved word. Headings matching these words will be
           updated to be suffixed with a '_".
       * named_tuple: initialized to None, but when the class is instantiated, an namedtuple will be created, building
           the name from the section name, and the list of identified elements.
    """
    elements = 'elements'
    reserved_names = 'reserved_names'
    named_tuple = 'named_tuple'
    illegal_varible_name_characters = ['#', '/', '-', '.', '$', '\\', '@', '*', '(', ')', '&', '^', '<', '>', '?',
                                       ',', '!', "'", '~', '`', '[', ']', '{', '}', '|', '+', '=', ':', ';']

    definitions = {
        ELFLogSections.CALL_STACK_INFORMATION: {
            elements: ['methods', 'details', 'stack', 'address', 'module', 'offset', 'unit', 'classname',
                       'procedure', 'line'],
            reserved_names: [],
            named_tuple: None,
        },

        ELFLogSections.EXCEPTION: {
            elements: ['date', 'address', 'module_name', 'module_version', 'type_', 'message', 'id_',
                       'sent'],
            reserved_names: ['type', 'id'],
            named_tuple: None,
        },

        ELFLogSections.ACTIVE_CONTROLS: {
            elements: ['form_class', 'form_text', 'control_class', 'control_text'],
            reserved_names: [],
            named_tuple: None,
        },

        ELFLogSections.COMPUTER: {
            elements: ['name', 'total_memory', 'free_memory', 'total_disk', 'free_disk', 'system_up_time',
                       'processor', 'display_mode', 'display_dpi', 'video_card', 'virtual_machine'],
            reserved_names: [],
            named_tuple: None,
        },

        ELFLogSections.USER: {
            elements: ['id_', 'name'],
            reserved_names: ['id'],
            named_tuple: None,
        },

        ELFLogSections.APPLICATION: {
            elements: ['start_date', "name_description", "version_number", "parameters", "compilation_date",
                       "up_time"],
            reserved_names: [],
            named_tuple: None,
        },

        ELFLogSections.OPERATING_SYSTEM: {
            elements: ['type_', 'build', 'update', 'non_unicode_language', 'charset_acp'],
            reserved_names: ['type'],
            named_tuple: None
        },

        ELFLogSections.MODULES: {
            elements: ['handle', 'name', 'description', 'version', 'size', 'modified', 'path'],
            reserved_names: [],
            named_tuple: None,
        },

        ELFLogSections.PROCESSES_INFORMATION: {
            elements: ['id_', 'name', 'description', 'version', 'memory', 'priority', 'threads', 'path'],
            reserved_names: ['id'],
            named_tuple: None,
        },

        ELFLogSections.ASSEMBLER_INFORMATION: {
            elements: [],
            reserved_names: [],
            named_tuple: None,
        },

        ELFLogSections.REGISTERS: {
            elements: [],
            reserved_names: [],
            named_tuple: None,
        },

        ELFLogSections.NETWORK: {
            elements: ['ip_address', 'submask', 'gateway', 'dns_1', 'dns_2', 'dhcp'],
            reserved_names: [],
            named_tuple: None,
        },

    }

    def __init__(self) -> typing.NoReturn:
        """
        Initialize the object and build the corresponding namedtuple for storing the section entries.
        """
        self._define_named_tuples()

    # noinspection PyTypeChecker
    def _define_named_tuples(self) -> typing.NoReturn:
        """
        Define the namedtuple for each section, name: {section name}Element, attributes: list of identified elements.

        :return: None.
        """
        for section_name in self.definitions:
            self.definitions[section_name][self.named_tuple] = namedtuple(
                self._build_tuple_name(section_name), self.get_elf_section_attribute_list(section_name))

    @staticmethod
    def _build_tuple_name(section: str) -> str:
        """
        Build the name of the namedtuple, using the SectionName (removing any spaces), and suffixing
        the section name with "Element"

            Example: "Section Name" --> SectionNameElement

        :param section: Name of section used to defined the namedtuple name.

        :return: (str) Name of namedtuple.

        """
        tuple_section_name = re.sub(r'\s+', '', section)
        return f"{tuple_section_name}Element"

    def get_tuple_definition(self, section: str) -> named_tuple:
        """
        Return the namedtuple definition for a given section.

        :param section: Name of section.

        :return: namedtuple for the provided section.

        """
        return self.definitions[section][self.named_tuple]

    def get_reserved_attribute_names(self, section: str) -> typing.List[str]:
        """
        Return a list of the python object-level reserved report elements for a given section.

        :param section: Name of section.

        :return: List of reserved python words for the provided section.

        """
        return self.definitions[section][self.reserved_names]

    @classmethod
    def get_elf_section_attribute_list(cls, section: str) -> typing.List[str]:
        """
        Return the list of report attributes (namedtuple attributes) for a given section.

        :param section: Name of section.

        :return: List of report (tuple) attributes for the provided section.

        """
        return cls.definitions[section][cls.elements]

    def remove_illegal_characters(self, string: str) -> str:
        """
        Remove any illegal characters from a string.

        Use case: The various section attributes are used as namedtuple variables, however, they may contain
          characters that are not allowed in a python variable (e.g. '-', '#', '$', '/', '.'). These are replaced
          with a space so the attribute can used as an attribute name in the namedtuple definition. (The spaces are
          later replaced with underscores, but is not done here, to deal with the case:

          Example:  "name      #  " --> would result in a rogue, mid-string underscore. By replacing with a space,
          when the trailing spaces are removed, the invalid character will not leave an artifact.

        :param string:  String to be inspected and illegal characters removed.

        :return: Updated string (without illegal characters)

        """
        for illegal_character in [x for x in self.illegal_varible_name_characters if x in string]:
            string = re.sub(illegal_character, ' ', string)
        return string.strip()


class ELFLogParser:
    """
    This is the primary logic for parsing the ELF logs. Many routines are generalized (as the section formats are
    identical. It executes the parsing routines based on the sections defined in the ELFLogSections class.
    Most methods are private (to simplify use).

    get_section_names_found: Get the list of sections found in the specified ELF log file.
            - raw (bool): True: the sections found while dividing the raw text into sections.
                          False (default): the sections parsed into data structures.

    get_section: Get a specific ELF log section, using the section names defined in the ELFLogSections class.
            - raw (bool): True: the raw text in the section of the log.
                          False (default): the processed list/dictionary of text, stored in specialized NamedTuples

    get_all_section: Get the entire log, returned a dictionary. Key =  the section names defined in ELFLogSections
             - raw (bool): True: the raw text in the section of the log.
                           False (default): the processed list/dictionary of text, stored in specialized NamedTuples

    """
    # Commonly used class variables
    SECTION_NAME = 'section_name'
    ATTRIBUTE = 'attribute'
    DATA = 'data'
    COLUMN_DELIMITER = '|'
    STACK_SECTION = 'stack'
    SUMMARY_SECTION = 'summary'

    # General Log Regexp Patterns
    LOG_SECTION_DELIMITER = re.compile(r'^(?P<section_name>\w[\w\d\s]+):[\r\n]*')
    TABLE_DELIMITER = re.compile(r'^[|]*-{12,}')
    DATA_LINE_PATTERN = re.compile(r'^\s*\d+\.\d+\s+(?P<attribute>.*?)\s*:\s*(?P<data>.*)?')

    def __init__(self, log_file: str = '', binary_content: str = '') -> None:
        """
        Initialize the object and parse the file.
        :param log_file: ELF Log file to parse.
        """
        self.log_file = log_file
        self._tuples = ELFDataTuples()

        if self.log_file != '':
            self._contents = self._read_file()
        elif binary_content != '':
            self._contents = self._process_data_stream(binary_content)
        else:
            raise UnableToParseELFLog('No ELF log filename or file contents provided.')

        self._raw_sections = self._parse_raw_sections()
        self._parsed_sections = self._parse_elf_sections()

    def _read_file(self) -> typing.List[str]:
        """
        Read the file.

        :return: List of lines from the file.
        """
        with open(self.log_file, "r", encoding='utf8') as ELF:
            return ELF.readlines()

    @staticmethod
    def _process_data_stream(stream: str) -> typing.List[str]:
        """
        Remove binary prefix in ELF log contents.

        :param stream: Data stream from getting attachment from Jira.

        :return: List of lines in file.

        """
        index = stream.find("Eureka")
        return [x for x in stream[index:].split('\\r\\n')]

    def _parse_raw_sections(self) -> typing.Dict[str, typing.List[str]]:
        """
        Sort the log file lines into lists, based on the section name.

        :return: Dictionary of lists:
            key: section name, value: list of lines in the that section.

        """
        sections = {}
        current_section = None
        for line in self._contents:

            # Check for a section header. If found, add it to dictionary: key: section_name, value: empty list
            # Also store the section name as current section name. All subsequent lines will be added to the
            # current section list until another section name is detected.
            match = self.LOG_SECTION_DELIMITER.search(line)
            if match is not None:
                current_section = match.group(self.SECTION_NAME)
                sections[current_section] = []

            elif current_section is not None:
                sections[current_section].append(line.strip())

        return sections

    def _parse_elf_sections(self) -> typing.Dict[str, typing.Any]:
        """
        For each section name listed in the ELFLogSection class, call the corresponding section's line parsing routine.
        Each log line parsing routine is responsible for providing the data.

        :return: Dictionary of lists of namedTuples per section.
            key: section_name value: list of namedtuples containing parsed data
                     (namedtuple definitions are specific to each section)

        """
        sections = {}
        for section_name in dataclasses.asdict(ELFLogSections()).keys():
            name = re.sub(r'\s+', '_', getattr(ELFLogSections, section_name)).lower()
            method_name = f'_parse_{name}_section'

            # If there is a method for parsing the specific section, call it.
            if hasattr(self, method_name):
                method = getattr(self, method_name)

                # If the method name exists in the class but is not callable (e.g. - stubbing var):
                # return an empty dictionary.
                sections[name] = method() if callable(method) else {}

            # No method found, so the section is not supported. (Thus needs to have support added).
            else:
                print(f"No method found for: {method_name}")

        return sections

    def get_section_names_found(self, raw: bool = False) -> typing.List[str]:
        """
        Return the list of sections found in the parsed ELF file.

        :param raw: Boolean: True: return list of sections found when breaking the data into sections.
                             False (default): return list of sections found when parsing the sections.

        :return: List of sections (str) found.

        """
        return list(self._raw_sections.keys()) if raw else list(self._parsed_sections.keys())

    def get_section(self, section_name: str, raw: bool = False) -> typing.Any:
        """
        Get a specific ELF report section.

        :param section_name: Name of the desired section (use ELFLogSection class attributes)
        :param raw: (bool) - True: return list of unparsed section log lines
                             False: return list of parsed section log lines (namedtuples).

        :raises: SectionNotFound

        :return: List of lines or namedTuples corresponding to the section provided.

        """
        data = self._raw_sections if raw else self._parsed_sections

        # If the section name is not in the data, replace mid-line spaces with underscores, in case the actual
        # section name was provided, rather than the ELFLogSection attribute.
        if section_name not in data:
            section_name = self._replace_space_with_char(section_name, "_").lower()

        # Get the data, if present
        if section_name in data:
            return data.get(section_name)

        raise SectionNotFound(section_name)

    def get_all_sections(self, raw=False) -> typing.Dict[str, typing.Any]:
        """
        Return all sections.

        :param: raw: (bool) - True: return list of unparsed section log lines
                              False: return list of parsed section log lines (namedtuples).

        :return: dictionary of all sections key: section_name, value: dict/list of data

        """
        return self._raw_sections if raw else self._parsed_sections

    def _parse_call_stack_information_section(self) -> typing.Dict[str, typing.Any]:
        """
        Internal parsing routine for CALL STACK INFORMATION section.

        :return:
            Dictionary of data:
                2 sets of key/values:
                + summary: string of stack summary (first portion of section table)
                + stack: list of stack trace calls (namedtuple per row: attributes = columns in table)
        """
        table_delimiter_count = 0
        stack_trace_summary_section = 2  # After second table delimiter, stack summary starts
        stack_trace_table_section = 3    # After third table delimiter, call stack starts

        parsed_data = {self.SUMMARY_SECTION: '', self.STACK_SECTION: []}

        # Get the raw data for the section
        section = ELFLogSections.CALL_STACK_INFORMATION
        raw_data = self.get_section(section, raw=True)

        for index, line in enumerate(raw_data):

            # Check for table section delimiter (and count how many instances currently encountered)
            match = self.TABLE_DELIMITER.search(line)
            if match is not None:
                table_delimiter_count += 1
                continue

            # Stack Trace Summary section
            if table_delimiter_count == stack_trace_summary_section:
                cleaned_line = line.strip(f' {self.COLUMN_DELIMITER}')
                parsed_data[self.SUMMARY_SECTION] += f"{cleaned_line}\n"

            # Stack Trace Table section
            stack_trace_tuple = self._tuples.get_tuple_definition(section)

            # For each line, create a list of elements, by breaking apart line on the delimiters Then pair each element
            # with the column header.
            # Column order specified in: ELFDataTuples.definition[section_name][elements] list
            if table_delimiter_count == stack_trace_table_section:
                stack_elements = [
                    elem.strip(f' {self.COLUMN_DELIMITER}') for elem in line.split(self.COLUMN_DELIMITER) if elem != ''
                ]
                parsed_data[self.STACK_SECTION].append(stack_trace_tuple(
                    **dict([(k, v) for k, v in
                            zip(self._tuples.get_elf_section_attribute_list(section), stack_elements)])))

        return parsed_data

    def _parse_modules_information_section(self) -> typing.List[namedtuple]:
        """
        Parse the MODULES INFORMATION section, which is a common format table.

        :return: List of section specific namedtuples, 1 namedtuple per row.

        """
        return self._parse_table(ELFLogSections.MODULES)

    def _parse_processes_information_section(self) -> typing.List[namedtuple]:
        """
        Parse the MODULES INFORMATION section, which is a common format table.

        :return: List of section specific namedtuples, 1 namedtuple per row.

        """
        return self._parse_table(ELFLogSections.PROCESSES_INFORMATION)

    def _parse_table(self, section: str) -> typing.List[namedtuple]:
        """
        Generic ELF log table parsing routine.

        :param section: Name of section to parse

        :return: List of section specific namedtuples, 1 namedtuple per row.

        """
        parsed_data = []
        data_tuple = self._tuples.get_tuple_definition(section)

        # Get section raw data
        raw_data = self.get_section(section, raw=True)
        header_delimiter_row = 0

        for line in raw_data:
            # The tables have a header column, so move to the next line if the second section header delimiter row has
            # not been parsed, and skip any subsequent row that does not have a column/data delimiter.
            # (possible additional sections or the end of the table).
            if self.COLUMN_DELIMITER not in line or header_delimiter_row < 2:
                header_delimiter_row += 1
                continue

            # For each line, create a list of elements, by breaking apart line on the delimiters Then pair each element
            # with the column header.
            # Column order specified in: ELFDataTuples.definition[section_name][elements] list.
            # NOTE: Splicing: [1:-1] -> On splitting the line with the delimiter, the first and last elements of the
            # list are '' since there was no character before the first or after the last. These are not data columns,
            # so they can be removed from the list.
            parts = [x.strip() for x in line.strip().split(self.COLUMN_DELIMITER)][1:-1]
            parsed_data.append(data_tuple(**dict(
                [(k, v) for k, v in zip(self._tuples.get_elf_section_attribute_list(section), parts)])))

        return parsed_data

    def _parse_exception_section(self) -> namedtuple:
        """
        Parse the EXCEPTION section of the ELF Log data.

        :return: List of section-specific namedtuples. One namedtuple per line.

        """
        return self._parse_general_section(section=ELFLogSections.EXCEPTION)

    def _parse_active_controls_section(self) -> namedtuple:
        """
        Parse the ACTIVE_CONTROL section of the ELF Log data.

        :return: List of section-specific namedtuples. One namedtuple per line.

        """
        return self._parse_general_section(section=ELFLogSections.ACTIVE_CONTROLS)

    def _parse_computer_section(self) -> namedtuple:
        """
        Parse the COMPUTER section of the ELF Log data.

        :return: List of section-specific namedtuples. One namedtuple per line.

        """
        return self._parse_general_section(section=ELFLogSections.COMPUTER)

    def _parse_user_section(self) -> namedtuple:
        """
        Parse the USER section of the ELF Log data.

        :return: List of section-specific namedtuples. One namedtuple per line.

        """
        return self._parse_general_section(section=ELFLogSections.USER)

    def _parse_application_section(self) -> namedtuple:
        """
        Parse the APPLICATION section of the ELF Log data.

        :return: List of section-specific namedtuples. One namedtuple per line.

        """
        return self._parse_general_section(section=ELFLogSections.APPLICATION)

    def _parse_operating_system_section(self) -> namedtuple:
        """
        Parse the OPERATING SYSTEM section of the ELF Log data.

        :return: List of section-specific namedtuples. One namedtuple per line.

        """
        return self._parse_general_section(section=ELFLogSections.OPERATING_SYSTEM)

    def _parse_registers_section(self) -> namedtuple:
        """
        Parse the REGISTERS section of the ELF Log data.

        :return: List of section-specific namedtuples. One namedtuple per line.

        """
        return self._parse_general_section(section=ELFLogSections.REGISTERS)

    def _parse_assembler_information_section(self) -> namedtuple:
        """
        Parse the ASSEMBLER INFORMATION section of the ELF Log data.

        :return: List of section-specific namedtuples. One namedtuple per line.

        """
        return self._parse_general_section(section=ELFLogSections.ASSEMBLER_INFORMATION)

    def _parse_general_section(self, section: str) -> namedtuple:
        """
        Generic section parsing routine. Many sections in the ELF log have the same basic format.

        :return: List of section-specific namedtuples. One namedtuple per line.

        """
        data_dict = {}

        # Get section data named tuple
        data_tuple = self._tuples.get_tuple_definition(section)

        if not self._tuples.get_elf_section_attribute_list(section):
            return data_tuple()

        raw_data = [line.strip() for line in self.get_section(section, raw=True) if line.strip() != '']

        # Parse each line of raw output and build dictionary of attribute: data
        for line in raw_data:

            match = self.DATA_LINE_PATTERN.search(line)
            if match is not None:
                # In the attribute name, replace any mid-string spaces with underscores
                # e.g.: "my example" --> "my_example"
                attribute = self._tuples.remove_illegal_characters(match.group(self.ATTRIBUTE).strip().lower())
                attribute = self._replace_space_with_char(string=attribute, char='_')

                # If the attribute name matches python reserved word, add an underscore as suffix
                # e.g.: id --> id_, type --> type_
                if attribute in self._tuples.get_reserved_attribute_names(section):
                    attribute = f'{attribute}_'
                attribute = self._tuples.remove_illegal_characters(attribute)

                # Store attribute in dictionary
                data_dict[attribute] = match.group(self.DATA).strip()

        return data_tuple(**data_dict)

    def _parse_network_section(self) -> typing.List[namedtuple]:
        """
        Parse the NETWORK section of the ELF log. This section contains a different format than all other sections.

        :return: List of namedtuples, one per interface (column). Attributes are defined 1 per row.

        """
        section = ELFLogSections.NETWORK

        temp_data = {}

        # Get the NETWORK sections namedtuple
        data_tuple = self._tuples.get_tuple_definition(section)

        # Get the network section raw data
        raw_data = self.get_section(section, raw=True)

        number_of_interfaces = 0  # The number of interfaces is based on the number of columns in the table.

        # Each row in the table is different attribute, common to all named tuples.
        # Parse each line into a dict of lists. key:attribute, value:list of values per attribute
        # (each element will map to a different interface)
        for line in raw_data:
            match = self.DATA_LINE_PATTERN.search(line)
            if match is not None:
                # Process the attribute name
                name = self._replace_space_with_char(match.group(self.ATTRIBUTE).lower(), "_")

                # Parse each column value into the row's list
                results = [x.strip() for x in match.group(self.DATA).split(' ')
                           if (x.strip() != '' and x.strip() != '-')]

                # The number of interfaces is equal to the number of parsed columns
                number_of_interfaces = len(results)
                temp_data[name] = results

        # Initialize tuple args list: number of tuples = number of interfaces
        tuple_args_dicts = [{} for _ in range(0, number_of_interfaces)]

        # For each interface, get the interface's attribute name and value.
        # Example: interface 0 will get the 0th element of each attribute.
        # Store in a list of dictionaries. Each dictionary is an interface: key: attribute value: attribute value.
        for tuple_number in range(0, number_of_interfaces):
            for key, values in temp_data.items():
                tuple_args_dicts[tuple_number][key] = values[tuple_number]

        # Build a list of NetworkElement namedtuples, one per interface
        return [data_tuple(**tuple_args_dict) for tuple_args_dict in tuple_args_dicts]

    @staticmethod
    def _replace_space_with_char(string: str, char: str) -> str:
        """
        Convenience method for replacing space characters ('\\s', '\\t') with different character(s).
        Typically used to translate log report attribute names into python allowable variables
        (e.g. - replace spaces with underscores).

        :param string: String to process
        :param char: Character(s) used to replace spaces.

        :return: String without space characters.

        """
        return re.sub(r'\s+', char, string)


if __name__ == '__main__':
    """
    Basic manual testing routine.
    Specify name of ELF log filespec as arg: ./elf_parser.py <ELF LOGFILE FILESPEC>
    """

    import pprint
    import sys

    # Default ELF if not specified
    # local_elf_file = ".\\elf logs\\BugReport_0A850000_20200511142348.el"
    # local_elf_file = ".\\elf logs\\BugReport_BC100000_20200522114153.el"
    local_elf_file = "../../elf logs/BugReport_2AFD0000_20200601151912.el"

    elf_file = sys.argv[2] if len(sys.argv) > 1 else local_elf_file

    # Section to test/verify
    target_section = ELFLogSections.MODULES

    # Read the file, list all sections defined in the ELFLogSections
    parser = ELFLogParser(elf_file)
    print(f"{ELFLogSections.list_sections()}\n")

    # List everything, then list section specific parsed data.
    print(f"EVERYTHING:\n{pprint.pformat(parser.get_all_sections())}")
    print(f"SECTION: {target_section}\n"
          f"{'-' * 80}\n"
          f"{pprint.pformat(parser.get_section(target_section))}")

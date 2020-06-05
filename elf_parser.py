from collections import namedtuple
import dataclasses
import pprint
import re
import typing


class SectionNotFound(Exception):
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
                                       ',', '!', "'", '~', '`', '[', ']', '{', '}', '|', '+', '=']

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
                self._build_tuple_name(section_name), self.get_attribute_list(section_name))

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

    def get_attribute_list(self, section: str) -> typing.List[str]:
        """
        Return the list of report (tuple) attributes for a given section.

        :param section: Name of section.

        :return: List of report (tuple) attributes for the provided section.

        """
        return self.definitions[section][self.elements]

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

    SECTION_NAME = 'section_name'
    ATTRIBUTE = 'attribute'
    DATA = 'data'
    COLUMN_DELIMITER = '|'

    # GENERAL LOG PATTERN
    LOG_SECTION_DELIMITER = re.compile(r'^(?P<section_name>[\w\s\d]+):[\r\n]')
    TABLE_DELIMITER = re.compile(r'^[|]*-{20,}')
    DATA_LINE_PATTERN = re.compile(r'^\s*[\d.]+\s+(?P<attribute>.*?)\s*:\s*(?P<data>.*)?')

    def __init__(self, log_file: str) -> typing.NoReturn:
        self.log_file = log_file
        self._tuples = ELFDataTuples()

        self._contents = self._read_file()
        self._raw_sections = self._parse_raw_sections()
        self._parsed_sections = self._parse_elf_sections()

    def _read_file(self) -> typing.List[str]:
        with open(self.log_file, "r", encoding='utf8') as ELF:
            return ELF.readlines()

    def _parse_raw_sections(self) -> typing.Dict[str, typing.List[str]]:
        sections = {}
        current_section = None
        for line in self._contents:
            match = self.LOG_SECTION_DELIMITER.search(line)
            if match is not None:
                current_section = match.group(self.SECTION_NAME)
                sections[current_section] = []
            elif current_section is not None:
                sections[current_section].append(line.strip())
        return sections

    def _parse_elf_sections(self) -> typing.Dict[str, typing.Any]:
        sections = {}
        for section_name in dataclasses.asdict(ELFLogSections()).keys():
            name = re.sub(r'\s+', '_', getattr(ELFLogSections, section_name)).lower()
            method_name = f'_parse_{name}_section'
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                sections[name] = method() if callable(method) else {}
            else:
                print(f"No method found for: {method_name}")
        return sections

    def get_section(self, section_name: str, raw: bool = False) -> typing.Any:
        data = self._raw_sections if raw else self._parsed_sections
        if section_name not in data:
            section_name = self._replace_space_with_char(section_name, "_").lower()

        if section_name in data:
            return data.get(section_name)
        raise SectionNotFound(section_name)

    def get_all_sections(self) -> typing.Dict[str, typing.Any]:
        return self._parsed_sections

    def _parse_call_stack_information_section(self) -> typing.Dict[str, typing.Any]:
        summary_section = 'summary'
        stack_section = 'stack'
        table_delimiter_count = 0
        stack_trace_summary_section = 2
        stack_trace_table_section = 3
        parsed_data = {summary_section: '', stack_section: []}

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
                parsed_data[summary_section] += f"{cleaned_line}\n"

            # Stack Trace Table section
            stack_trace_tuple = self._tuples.get_tuple_definition(section)
            if table_delimiter_count == stack_trace_table_section:
                stack_elements = [elem.strip(f' {self.COLUMN_DELIMITER}') for elem in line.split(self.COLUMN_DELIMITER)
                                  if elem != '']
                parsed_data[stack_section].append(stack_trace_tuple(
                    **dict([(k, v) for k, v in zip(self._tuples.get_attribute_list(section), stack_elements)])))

        return parsed_data

    def _parse_modules_information_section(self) -> typing.List[namedtuple]:
        return self._parse_table(ELFLogSections.MODULES)

    def _parse_processes_information_section(self) -> typing.List[namedtuple]:
        return self._parse_table(ELFLogSections.PROCESSES_INFORMATION)

    def _parse_table(self, section: str) -> typing.List[namedtuple]:
        parsed_data = []
        data_tuple = self._tuples.get_tuple_definition(section)

        raw_data = self.get_section(section, raw=True)
        header_delimiter_row = 0
        for line in raw_data:
            if self.COLUMN_DELIMITER not in line or header_delimiter_row < 2:
                header_delimiter_row += 1
                continue
            parts = [x.strip() for x in line.strip().split(self.COLUMN_DELIMITER)][1:-1]
            parsed_data.append(data_tuple(**dict(
                [(k, v) for k, v in zip(self._tuples.get_attribute_list(section), parts)])))
        return parsed_data

    def _parse_exception_section(self) -> namedtuple:
        return self._parse_general_section(section=ELFLogSections.EXCEPTION)

    def _parse_active_controls_section(self) -> namedtuple:
        return self._parse_general_section(section=ELFLogSections.ACTIVE_CONTROLS)

    def _parse_computer_section(self) -> namedtuple:
        return self._parse_general_section(section=ELFLogSections.COMPUTER)

    def _parse_user_section(self) -> namedtuple:
        return self._parse_general_section(section=ELFLogSections.USER)

    def _parse_application_section(self) -> namedtuple:
        return self._parse_general_section(section=ELFLogSections.APPLICATION)

    def _parse_operating_system_section(self) -> namedtuple:
        return self._parse_general_section(section=ELFLogSections.OPERATING_SYSTEM)

    def _parse_registers_section(self) -> namedtuple:
        return self._parse_general_section(section=ELFLogSections.REGISTERS)

    def _parse_assembler_information_section(self) -> namedtuple:
        return self._parse_general_section(section=ELFLogSections.ASSEMBLER_INFORMATION)

    def _parse_general_section(self, section: str) -> namedtuple:
        data_dict = {}

        # Get section data named tuple
        data_tuple = self._tuples.get_tuple_definition(section)

        if not self._tuples.get_attribute_list(section):
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
        section = ELFLogSections.NETWORK
        data_tuple = self._tuples.get_tuple_definition(section)

        temp_data = {}
        raw_data = self.get_section(section, raw=True)
        number_of_interfaces = 0
        for line in raw_data:
            match = self.DATA_LINE_PATTERN.search(line)
            if match is not None:
                name = self._replace_space_with_char(match.group(self.ATTRIBUTE).lower(), "_")
                results = [x.strip() for x in match.group(self.DATA).split(' ')
                           if (x.strip() != '' and x.strip() != '-')]
                number_of_interfaces = len(results)
                temp_data[name] = results

        # Initialize tuple args list: number of tuples = number of interfaces
        tuple_args_dicts = [{} for _ in range(0, number_of_interfaces)]

        for tuple_number in range(0, number_of_interfaces):
            for key, values in temp_data.items():
                tuple_args_dicts[tuple_number][key] = values[tuple_number]

        return [data_tuple(**tuple_args_dict) for tuple_args_dict in tuple_args_dicts]

    @staticmethod
    def _replace_space_with_char(string: str, char: str) -> str:
        return re.sub(r'\s+', char, string)


if __name__ == '__main__':
    import sys
    local_elf_file = ".\\elf logs\\BugReport_0A850000_20200511142348.el"
    # local_elf_file = ".\\elf logs\\BugReport_BC100000_20200522114153.el"

    elf_file = sys.argv[2] if len(sys.argv) > 1 else local_elf_file

    target_section = ELFLogSections.MODULES

    parser = ELFLogParser(elf_file)
    print(f"{ELFLogSections.list_sections()}\n")
    print(f"EVERYTHING:\n{pprint.pformat(parser.get_all_sections())}")
    print(f"SECTION: {target_section}\n"
          f"{'-' * 80}\n"
          f"{pprint.pformat(parser.get_section(target_section))}")

from collections import namedtuple
import re
import typing

from MDCBR.elf.elf_log_sections import ELFLogSections


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
    illegal_variable_name_characters = ['#', '/', '-', '.', '$', '\\', '@', '*', '(', ')', '&', '^', '<', '>', '?',
                                        ',', '!', "'", '~', '`', '[', ']', '{', '}', '|', '+', '=', ':', ';']

    definitions = {
        ELFLogSections.CALL_STACK_INFORMATION: {
            elements: ['methods', 'details', 'stack', 'address', 'module', 'offset', 'unit', 'classname', 'procedure',
                       'line'],
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
        for illegal_character in [x for x in self.illegal_variable_name_characters if x in string]:
            string = re.sub(illegal_character, ' ', string)
        return string.strip()

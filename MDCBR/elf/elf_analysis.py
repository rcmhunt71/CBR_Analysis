import pprint
import typing

from MDCBR.elf.elf_parser import ELFDataTuples, ELFLogSections


class ELFAnalysis:
    """

    The purpose of this class is to provide the logic to compare and sort failures/stack traces reported in
    ELF (Eureka Log Files) log files.

    """
    # Used in creating unique call stack id string
    STACK_ELEMENT_DELIMITER = ', '

    def __init__(self, data_struct: typing.Dict[str, dict]) -> typing.NoReturn:
        self.data_struct = data_struct
        self.call_stacks = {}

    def perform_stack_trace_assessment(self) -> typing.Dict[str, typing.List[str]]:
        """
        Marshall the callstack into a string, and store all callstack_strings in a dictionary as keys.
        The each dictionary value will be a list of defect_ids matching the callstack_string.

        The callstack_string is made up of several elements in each call stack frame. See
        ELFAnalysis._build_call_stack_proc_list for the specific elements used.

        :return: Dictionary of callstack_strings -> List of defect_ids

        """
        # For each JIRA defect object in the data set...
        for defect_id, data in self.data_struct.items():

            # Get the call stack info, convert to list of specific call stack elements, and create str
            stack_info = self._build_call_stack_proc_list(data.get(ELFLogSections.CALL_STACK_INFORMATION))
            stack_info_key = self.STACK_ELEMENT_DELIMITER.join(stack_info)

            # If the call stack has not been seen before, initial value as empty dictionary
            if stack_info_key not in self.call_stacks:
                self.call_stacks[stack_info_key] = []

            # Store defect ID according to callstack_string
            self.call_stacks[stack_info_key].append(defect_id)

        return self.call_stacks

    def _build_call_stack_proc_list(self, call_stack: list) -> typing.List[str]:
        """
        Build a list of strings using elements from each frame in the call stack.
        :param call_stack: a list of call_stack tuples, one per frame of the call stack.

        :return: List of strings: each element = a frame in the call stack

        """
        # Elements to be used to create callstack_str
        target_elements = ['procedure', 'classname', 'unit']
        frame_delimiter = ':'

        # If target elements are not defined in the CALL_STACK_INFORMATION named tuple,
        # the analysis cannot be done.
        if not self._are_required_elements_defined(
                target_elements, ELFLogSections.CALL_STACK_INFORMATION):
            return []

        proc_info_data = []
        unit_info_data = []
        class_info_data = []

        # Store specific elements from each frame in the call stack into lists to be joined
        for call_stack_element in call_stack:
            proc_info_data.append(getattr(call_stack_element, target_elements[0]))
            class_info_data.append(getattr(call_stack_element, target_elements[1]))
            unit_info_data.append(getattr(call_stack_element, target_elements[2]))

        # List of stack frames: Frame info format: 'unit':'class':'procedure'
        return [f"{u_info}{frame_delimiter}{c_info}{frame_delimiter}{p_info}" for p_info, c_info, u_info in
                zip(proc_info_data, class_info_data, unit_info_data)]

    @staticmethod
    def _are_required_elements_defined(target_elements: typing.List[str], elf_section: str) -> bool:
        """
        Verify the elements to be used are defined in the namedtuple.
        :param target_elements: List of tuple elements
        :param elf_section: Name of section (which maps to a specific named tuple)

        :return: Boolena; True=all elemnents are defined in the namedtuplpe, False: error
        """

        # Convert name of desired elements and defined elements into sets
        target_attribute_set = set(target_elements)
        known_attributes_set = set(ELFDataTuples.get_elf_section_attribute_list(elf_section))

        # If the length of the set intersection matches the set of desired elements, all elements are defined.
        match = len(target_attribute_set.intersection(known_attributes_set)) == len(target_elements)

        if not match:
            print(f"ERROR: The following '{elf_section}' section attributes were not found:"
                  f" {target_attribute_set - known_attributes_set}")

        return match


if __name__ == '__main__':
    import json

    # Variables and Constants
    CALL_STACK = 'call_stack'
    section = ELFLogSections.CALL_STACK_INFORMATION
    translate = {}
    call_stacks = {}

    # Data file to read (rather than poll Jira each time)
    data_file = "../../CBR.data.json.txt"

    # Defects to assess
    defect_review = [2419, 2418, 2417, 2424]

    elf_tuple_defs = ELFDataTuples()
    tuple_def = elf_tuple_defs.get_tuple_definition(section)

    # Read data file
    with open(data_file, "r") as JSON_DATA_FILE:
        data_obj = json.load(JSON_DATA_FILE)

    # Iterate through data and build list of namedtuples based on the specified section
    for defect_id, data in data_obj.items():
        translate[defect_id] = {}
        translate[defect_id][section] = [tuple_def(**stack_dict) for stack_dict in data[CALL_STACK]]
        # if int(defect_id.split('-')[-1]) in defect_review:
        #     print(f"DEFECT: {defect_id}:\n{pprint.pformat(translate[defect_id])}")

    # Do analysis (categorize/compare stack traces)
    elf_analysis = ELFAnalysis(data_struct=translate)
    elf_analysis.perform_stack_trace_assessment()

    # Print results based on specific defect id
    for defect in defect_review:
        for call_stack, defect_ids in elf_analysis.call_stacks.items():
            if f'CBR-{defect}' in defect_ids:
                print(f"DEFECT CBR-{defect}:\n{pprint.pformat(call_stack)}\n")

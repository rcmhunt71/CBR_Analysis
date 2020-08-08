import pprint

from MDCBR.elf.elf_parser import ELFDataTuples, ELFLogSections, ELFLogParser


class ELFAnalysis:
    """

    The purpose of this class is to provide the logic to compare and sort failures/stack traces reported in
    ELF (Eureka Log Files) log files.

    """
    def __init__(self, data_list):
        self.data_list = data_list

    def perform_stack_trace_assessment(self):
        stack_info = self._build_call_stack_proc_list()
        pprint.pprint(stack_info)

    def _build_call_stack_proc_list(self):
        target_elements = ['procedure', 'unit']

        if not self._are_required_elements_defined(
                target_elements, ELFLogSections.CALL_STACK_INFORMATION):
            return []

        proc_info_data = []
        unit_info_data = []
        for data_tuple in self.data_list.get(ELFLogParser.STACK_SECTION):
            proc_info_data.append(getattr(data_tuple, target_elements[0]))
            unit_info_data.append(getattr(data_tuple, target_elements[1]))

        # Stack info format: unit.procedure
        return [f"{p_info}:{u_info}" for p_info, u_info in zip(proc_info_data, unit_info_data)]

    @staticmethod
    def _are_required_elements_defined(target_elements, elf_section):
        target_attribute_set = set(target_elements)
        known_attributes_set = set(ELFDataTuples.get_elf_section_attribute_list(elf_section))

        if len(target_attribute_set.intersection(known_attributes_set)) != len(target_elements):
            print(f"ERROR: The following '{elf_section}' section attributes were not found:"
                  f" {target_attribute_set - known_attributes_set}")
            return False

        # print(f"Attributes found: {target_elements}")
        return True


if __name__ == '__main__':
    import elf_parser

    elf_file = "../../elf logs/BugReport_2AFD0000_20200601151912.el"
    section = ELFLogSections.CALL_STACK_INFORMATION

    parsed_elf = elf_parser.ELFLogParser(elf_file)

    elf_analysis = ELFAnalysis(data_list=parsed_elf.get_section(section))
    elf_analysis.perform_stack_trace_assessment()


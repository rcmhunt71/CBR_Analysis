import json
from MDCBR.elf.elf_parser import ELFLogSections, ELFLogParser, ELFDataTuples


def issue_list_to_file(issue_list, data_file, section, debug=False):
    call_stack_keyword = "call_stack"
    err_msg_keyword = "err_msg"
    exception_type_keyword = "exception"
    version_keyword = "version"
    elements_keyword = ELFDataTuples.elements
    stack_keyword = ELFLogParser.STACK_SECTION
    section = ELFLogParser.convert_section_type_to_key(section)
    call_stack_tuple_elems = ELFDataTuples.definitions[ELFLogSections.CALL_STACK_INFORMATION][elements_keyword]

    if debug:
        print(f"ELEMENTS: {call_stack_tuple_elems}")
        print(f"SECTION: {section}")

    defect_stacks = {}
    for defect in issue_list:
        bug = dict()
        bug[exception_type_keyword] = defect.exception_type
        bug[version_keyword] = defect.version
        bug[call_stack_keyword] = []
        bug[err_msg_keyword] = defect.error_msg if defect.general_error_msg is None else defect.general_error_msg
        bug[call_stack_keyword] = [stack._asdict() for stack in
                                   defect.elf_log_model.get_section(section)[stack_keyword]]
        defect_stacks[defect.defect_id] = bug

    with open(data_file, "w") as DATA_FILE:
        json.dump(defect_stacks, DATA_FILE)

    print(f"\nWrote to: {data_file}")

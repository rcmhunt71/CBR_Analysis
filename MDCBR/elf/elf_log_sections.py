import dataclasses
import typing


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

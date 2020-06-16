

class ELFAnalysis:
    """

    The purpose of this class is to provide the logic to compare and sort failures/stack traces reported in
    ELF (Eureka Log Files) log files.

    """
    def __init__(self, exception_type, data_list):
        self.exception_type = exception_type
        self.data_list = data_list


if __name__ == '__main__':
    pass

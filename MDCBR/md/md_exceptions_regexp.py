import re


class MDExceptions:
    """
    These are the various Mortgage Director exceptions (these have been seen, but there could be additional
    exceptions which should be added here.

    The "GENERAL_EXCEPTION_PATTERN" removes the server information and matches the remainder of the msg for
    additional parsing.

    * <EXCEPTION>s are based on the exception type listed in the defect summary (title). The corresponding parsing
    patterns are stored as a list: <EXCEPTION>_PARSE.

    * The various <EXCEPTION>_PARSE elements are lists of regular expression patterns, matching the various
    messages that have been seen with the exception.

    """

    # For consistency, this is the name of the "named pattern" to extract user-added data from the description.
    # It is defined here so external classes can reference the "extra data" without worrying if the named_group name
    # changes later.
    EXTRA = 'extra'

    # All exception messages have the server name. This pattern removes the server name and returns the remainder of
    # the message.
    GENERAL_EXCEPTION_PATTERN = re.compile(
        r'server hostname:.*?[\r\n]+(?P<error_msg>.*)',
        re.IGNORECASE | re.DOTALL)

    # ----------------------------------------------------------------------------------------
    # <EXCEPTION_NAME>_PARSE regular expression pattern lists - stored in alphabetical order.
    # ----------------------------------------------------------------------------------------
    EABSTRACTERROR_PARSE = [
        re.compile(r'.*abstract error\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL)
    ]

    EACCESSVIOLATION_PARSE = [
        re.compile(
            r'address\s+(?P<violation_address>[\w\d]+)\.?\s*'
            r'(in module\s*\'[\w\d.]+\'\.)?'
            r'\s*.* of address\s*(?P<address>[\d\w]+)\.(?P<extra>.*)?',
            re.IGNORECASE | re.DOTALL),
    ]

    EARGUMENTEXCEPTION_PARSE = GENERAL_EXCEPTION_PATTERN
    EARGUMENTOUTOFRANGEEXCEPTION_PARSE = GENERAL_EXCEPTION_PATTERN
    ECONVERTERROR_PARSE = GENERAL_EXCEPTION_PATTERN

    EDATABASEERROR_PARSE = [
        re.compile(r'\'(?P<value>.*)\'\s+is not a valid .* value for field \'.*\'\.(?P<extra>.*)?',
                   re.IGNORECASE | re.DOTALL),
        re.compile(r'((?P<form>.*): )?cannot modify a read-only dataset\.(?P<extra>.*)?',
                   re.IGNORECASE | re.DOTALL),
        re.compile(r'Bookmark not found (?P<bookmark>.*)', re.IGNORECASE | re.DOTALL),
        re.compile(r'.*\.(\s.*\.)?(?P<extra>.*)?', re.IGNORECASE | re.DOTALL)
    ]

    EDIRECTORYNOTFOUNDEXCEPTION_PARSE = GENERAL_EXCEPTION_PATTERN
    EDOMPARSEERROR_PARSE = GENERAL_EXCEPTION_PATTERN

    EEXTERNALEXCEPTION_PARSE = [
        re.compile(r'address\s+(?P<violation_address>[\w\d]+).*'
                   r'address\s+(?P<read_address>[\w\d]+).*'
                   r'address:\s+(?P<v_address>[\w\d]+)\s+\((?P<r_address>[\w\d]+)\)\.'
                   r'(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),

        re.compile(r'stack overflow.*module:\s*.*\.(exe|dll).*code:.*address:'
                   r' (?P<address>[\w\d]+)\s+(?P<another_address>[\w\d]+)\.(?P<extra>.*)?',
                   re.IGNORECASE | re.DOTALL),
    ]

    EFCREATEERROR_PARSE = GENERAL_EXCEPTION_PATTERN
    EFOPENERROR_PARSE = GENERAL_EXCEPTION_PATTERN

    EIHMCUSTOMEXCEPTION_PARSE = [
        re.compile(
            r'.*'
            r'^thread id =(?P<thread_id>\d+).*'
            r'^.*dataset name = [\w\d]+$'
            r'.*'
            r'^cannot.*\]\.'
            r'(?P<extra>.*)?',
            re.IGNORECASE | re.MULTILINE | re.DOTALL),

        re.compile(
            r'.*thread id =(?P<thread_id>\d+)\s*^'
            r'dataset name = [\w\d]+\s*^'
            r'.*after login:.*\.(?P<extra>.*)?',
            re.IGNORECASE | re.DOTALL | re.MULTILINE),

        re.compile(
            r'.*thread id =(?P<thread_id>\d+)\s*^'
            r'dataset name = [\w\d]+\s*^'
            r'.*invalid variant operation\.'
            r'(?P<extra>.*)?',
            re.IGNORECASE | re.DOTALL | re.MULTILINE),
    ]

    EINOUTERROR_PARSE = [
        re.compile(r'.*create file\s+"(?P<filename>[\w\d.\\:]+)"\..*process.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),
    ]

    EINTOVERFLOW_PARSE = GENERAL_EXCEPTION_PATTERN

    EINVALIDCAST_PARSE = [
        re.compile(r'.*typecast\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL)
    ]

    EINVALIDGRIDOPERATION_PARSE = GENERAL_EXCEPTION_PATTERN

    EINVALIDOPERATION_PARSE = [
        re.compile(r'.*no parent window\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),
        re.compile(r'.*disabled or invisible window\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),
    ]

    EINVALIDPOINTER_PARSE = GENERAL_EXCEPTION_PATTERN

    EJCLANSISTRINGLISTERROR_PARSE = [
        re.compile(r'.*index out of bounds\s*\((?P<index>\d+)\)\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),
    ]

    ELISTERROR_PARSE = [
        re.compile(r'.*index out of bounds\s*\((?P<index>\d+)\).*?\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),
    ]

    EOLEERROR_PARSE = GENERAL_EXCEPTION_PATTERN

    EOSERROR_PARSE = [
         re.compile(r'.*code:\s+\d+\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL)
    ]

    EOSNOMOREFILES_PARSE = GENERAL_EXCEPTION_PATTERN
    EOSSUCCESS_PARSE = GENERAL_EXCEPTION_PATTERN
    EPRINTER_PARSE = GENERAL_EXCEPTION_PATTERN
    EPRIVILEGE_PARSE = [
        re.compile(r'.*privileged instruction\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL)
    ]
    ERANGEERROR_PARSE = [
        re.compile(r'.*range check error\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL)
    ]
    EREADERROR_PARSE = [
        re.compile(r'.*read error\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL)
    ]

    ESTRINGLISTERROR_PARSE = [
        re.compile(r'.*out of bounds \((?P<index>\d+)\)\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL)
    ]

    ETHREAD_PARSE = GENERAL_EXCEPTION_PATTERN

    ETIFFEXCEPTION_PARSE = [
        re.compile(r'.*dimensions exceeded\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL)
    ]

    EVARIANTARRAYCREATEERROR_PARSE = GENERAL_EXCEPTION_PATTERN
    EVARIANTBADINDEXERROR_PARSE = GENERAL_EXCEPTION_PATTERN
    EVARIANTBADVARTYPEERROR_PARSE = GENERAL_EXCEPTION_PATTERN
    EVARIANTINVALIDARGERROR_PARSE = GENERAL_EXCEPTION_PATTERN

    EXCEPTION_PARSE = [
        re.compile(r'at address\s+(?P<v_address>[\w\d]+)\s+.*'
                   r'of address\s+(?P<r_address>[\w\d]+)\.(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),

        re.compile(r'.*?[\r\n]+(?P<extra>.*)?', re.IGNORECASE | re.DOTALL),
    ]

    EXMLDOCERROR_PARSE = GENERAL_EXCEPTION_PATTERN
    EOLEEXCEPTION_PARSE = GENERAL_EXCEPTION_PATTERN
    EOLESYSERROR_PARSE = GENERAL_EXCEPTION_PATTERN
    EVARIANTINVALIDOPERROR_PARSE = GENERAL_EXCEPTION_PATTERN

import re
from mutate.utility import is_float, is_int

symbols = ['!', '@', '#', '$', '%', '&', '^', '*']
oparators = ['+', '-', '*', '/', '=', '+=', '-=', '==', '<', '>', '<=', '>=']
keywords = [
    "alignas", "alignof", "and", "and_eq", "asm", "atomic_cancel",
    "atomic_commit", "atomic_noexcept", "auto", "bitand", "bitor",
    "bool", "break", "case", "catch", "char", "char16_t", "char32_t",
    "class", "compl", "const", "constexpr", "const_cast", "continue",
    "decltype", "default", "delete", "do", "double", "dynamic_cast",
    "else", "enum", "explicit", "export", "extern", "false", "float",
    "for", "friend", "goto", "if", "inline", "int", "long", "mutable",
    "namespace", "new", "noexcept", "not", "not_eq", "nullptr",
    "operator", "or", "or_eq", "private", "protected", "public",
    "reflexpr", "register", "reinterpret_cast", "requires", "return",
    "short", "signed", "sizeof", "static", "static_assert",
    "static_cast", "struct", "switch", "synchronized", "template",
    "this", "thread_local", "throw", "true", "try", "typedef", "typeid",
    "typename", "union", "unsigned", "using", "virtual", "void",
    "volatile", "wchar_t", "while", "xor", "xor_eq",
]
delimiters = [' ', '	', '.', ',', '\n', ';',
              '(', ')', '<', '>', '{', '}', '[', ']']

std_function = [
    "main", "assert",
    # ctype
    "isalnum", "isalpha", "isdigit", "isspace", "islower",
    "isupper", "isxdigit", "iscntrl", "isprint", "ispunct",
    "isgraph", "tolower", "toupper",
    # math
    "acos", "asin", "atan", "atan2", "cos", "cosh", "sin", "sinh",
    "tanh", "exp", "frexp", "ldexp", "log", "log10", "modf", "pow",
    "sqrt", "ceil", "fabs", "floor", "fmod",
    # stdlib
    "atof", "atoi", "atol", "strtod", "strtol", "strtoul",
    "calloc", "free", "malloc", "realloc", "abort", "atexit", "exit",
    "getenv", "system", "bsearch", "qsort", "abs", "div", "labs", "ldiv",
    "rand", "srand", "mblen", "mbstowcs", "mbtowc", "wcstombs", "wctomb",
    # stdio
    "fclose", "clearerr", "feof", "ferror", "fflush", "fgetpos", "fopen",
    "fread", "freopen", "fseek", "fsetpos", "ftell", "fwrite", "remove",
    "rename", "rewind", "setbuf", "setvbuf", "tmpfile", "tmpnam", "fprintf",
    "printf", "sprintf", "vfprintf", "vprintf", "vsprintf", "fscanf",
    "scanf", "sscanf", "gfetc", "fgets", "fputc", "fputs", "getc", "getchar",
    "gets", "putc", "putchar", "puts", "ungetc", "perror",
    # string
    "memchr", "memcmp", "memcpy", "memmove", "memset",
    "strcat", "strncat", "strchr", "strcmp", "strncmp",
    "strcoll", "strcpy", "strncpy", "strcspn", "strerror",
    "strlen", "strpbrk", "strrchr", "strspn", "strstr",
    "strtok", "strxfrm", "strdup", "strndup",
    # iostream
    "cin", "wcin", "cout", "wcout", "cerr", "wcerr",
    "clog", "wclog", "endl",
]


def parsing(code):
    in_identifiers = dict()
    in_strings = dict()
    in_ints = dict()
    in_floats = dict()
    in_others = dict()
    line_breaks = []

    tokens = dict()
    isStr = None
    isWord = False
    token = ''

    for i, character in enumerate(code):
        if character == '"' or character == "'":
            if isStr is not None:
                if isStr == character:
                    token += character
                    tokens[i+1-len(token)] = token
                    token = ''
                    isStr = None
                else:
                    token = token+character
            else:
                if token:
                    tokens[i-len(token)] = token
                    token = ''
                isStr = character
                token += character

        elif isStr is not None:
            token = token+character

        elif character in symbols:
            if token:
                tokens[i-len(token)] = token
                token = ''
            tokens[i] = character

        elif character.isalnum() and not isWord:
            isWord = True
            assert(token == "")
            token = character

        elif character == '.' and isWord and token:
            if is_float(token+character):
                token += character

        elif (character in delimiters) or (character in oparators):
            if token:
                tokens[i-len(token)] = token
                token = ''

            if not (character == ' ' or character == '\n' or character == '	'):
                tokens[i] = character

            if character == '\n':
                line_breaks.append(i)

        elif isWord:
            token += character

    for index, value in tokens.items():
        if value[0] == "'" or value[0] == '"':
            if value not in in_strings:
                in_strings[value] = [index, ]
            else:
                in_strings[value].append(index)

        elif value in symbols:
            pass

        elif value in oparators:
            pass

        elif value in keywords:
            pass

        elif value in std_function:
            pass

        elif re.search("^[_a-zA-Z][_a-zA-Z0-9]*$", value):
            if value not in in_identifiers:
                in_identifiers[value] = [index, ]
            else:
                in_identifiers[value].append(index)

        elif value in delimiters:
            pass

        elif is_float(value):
            if is_int(value):
                if value not in in_ints:
                    in_ints[value] = [index, ]
                else:
                    in_ints[value].append(index)
            else:
                if value not in in_floats:
                    in_floats[value] = [index, ]
                else:
                    in_floats[value].append(index)

        else:
            in_others[value] = [index, ]

    ret = {
        "strings": in_strings,
        "ints": in_ints,
        "floats": in_floats,
        "identifiers": in_identifiers,
        "line_breaks": line_breaks,
    }
    return ret
import re, csv, os
from sys import stdin
from time import sleep

USE_COLORAMA = False
TERMINAL_SIZE = 0
PROGRESS_BAR_LEN = 0
try:
    TERMINAL_SIZE = (os.get_terminal_size().columns - 2) if stdin.isatty() else 0
    PROGRESS_BAR_LEN = TERMINAL_SIZE - 20
except:
    pass
try:
    from colorama import init, Fore, Style
    init()
    USE_COLORAMA = True
except:
    pass

DELIMITER_CHAR = '→'
ESCAPE_CHAR = '¶'
USE_CR_REPLACER = False
CARRIAGE_RETURN_REPLACER = '▒' #\u2592
CARRIAGE_RETURN = '\x0D'
CSV_ENCODING = "utf-8-sig"

MAX_LINES_CHARDET = 100 # reasonable depth of first foreign characters (lines)

FULL_RE = r'((?:\\(?:b|t|n|f|r|\"|\\)|\\'
PART_RE = r'((?:\\'
ESCAPECHARS_RE = re.compile(FULL_RE + r'(?:(?:[0-2][0-9]{1,2}|3[0-6][0-9]|37[0-7]|[0-9]{1,2}))|\\(?:u(?:[0-9a-fA-F]{4,8})))+)')

DIALECT_EXCEL = "excel"
DIALECT_TRANSLATION = "translation"
csv.register_dialect(DIALECT_EXCEL, delimiter='\t', doublequote=False, quotechar='\uffff', quoting=csv.QUOTE_NONE, escapechar='"', lineterminator='\n')
csv.register_dialect(DIALECT_TRANSLATION, delimiter=DELIMITER_CHAR, quotechar='\uffff', doublequote=False, quoting=csv.QUOTE_NONE, escapechar=ESCAPE_CHAR, lineterminator='\n')

LAST_NEWLINE_RE = re.compile(r"([^\n])[\n]$")


def chomp(x):
    """ Removes last linebreak after a character """
    LAST_NEWLINE_RE.sub(r'\1', x)
    return x


def num_groups(aregex):
    """ Counts groups in regexp """
    return re.compile(aregex).groups


def merge_dicts(*dict_args) -> dict:
    """ Merges several dict()s """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def preprocess_in(lines, replace_cr):
    for line in lines:
        if replace_cr:
            yield line.replace(CARRIAGE_RETURN, CARRIAGE_RETURN_REPLACER)
        else:
            yield line


def preprocess_out(lst, replace_cr):
    for row in lst:
        if replace_cr:
            yield [(col.replace(CARRIAGE_RETURN_REPLACER, CARRIAGE_RETURN) if isinstance(col, str) else col) for col in row]
        else:
            yield row


def read_csv_list(fn, ftype=DIALECT_TRANSLATION, replace_cr=USE_CR_REPLACER) -> list:
    """ Reads CSV array in a->b->... format """
    if os.path.isfile(fn):
        with open(fn, 'r', newline='', encoding=CSV_ENCODING) as f:
            return list(x for x in csv.reader(preprocess_in(f, replace_cr), ftype) if len(x) > 0)
    else:
        return list()


def write_csv_list(fn, lst, ftype=DIALECT_TRANSLATION, replace_cr=USE_CR_REPLACER):
    """ Writes CSV array in a->b->... format """
    if not lst or len(lst) == 0: return
    with open(fn, 'w', newline='', encoding=CSV_ENCODING) as f:
        writer = csv.writer(f, ftype)
        for row in preprocess_out(lst, replace_cr):
            writer.writerow(row)


def read_csv_dict(fn, ftype=DIALECT_TRANSLATION, replace_cr=USE_CR_REPLACER) -> dict:
    """ Reads CSV dictionary in a->b format """
    if os.path.isfile(fn):
        with open(fn, 'r', newline='', encoding=CSV_ENCODING) as f:
            # the function will ignore columns after second
            return {item[0]: item[1] for item in csv.reader(preprocess_in(f, replace_cr), ftype) if len(item) > 1}
    else:
        return dict()

#def string_unescape(s, enc="utf-8"):
#    return (bytes(s.encode("latin-1", "backslashreplace").decode("unicode_escape"), encoding=enc).decode(enc))

def string_unescape(s: str, encoding: str="utf-8") -> str:
    """ Unescapes backslash-escaped character sequences in strings """
    """
    sarray = ESCAPECHARS_RE.split(s)
    for i, si in enumerate(sarray):
        if ESCAPECHARS_RE.search(si):
            sarray[i] = si.encode("latin1").decode("unicode-escape")
    return ''.join(sarray)
    """
    return s.encode(encoding).decode( 'unicode-escape' )


def print_progress(index, total, type_of_progress=0, start_from=0, end_with=100, title=''):
    """ Prints progress bar

    index is expected to be 0 based current index.
    total total number of items.
    type_of_progress type of progress indicator element
    start_from starting percent
    end_with ending percent
    title header of the progressbar
    """
    if TERMINAL_SIZE == 0 or PROGRESS_BAR_LEN < 10:
        return

    if index > total: index = total
    elif index < 0: index = 0

    if start_from > total - 1 or start_from < 0: start_from = 0
    if end_with > 100 or end_with < 0: end_with = 100

    real_percent = index / total
    percent_range = (end_with - start_from)/100
    percent_done = min(100, start_from + 100 * real_percent *  percent_range)
    done = round(PROGRESS_BAR_LEN * percent_done // 100)

    done_str = None
    if type_of_progress == 0 or not USE_COLORAMA:
        done_str = '█' * int(done)
    elif type_of_progress == 1:
        done_str = Fore.LIGHTBLUE_EX + '█' * int(done) + Style.RESET_ALL
    elif type_of_progress == 2:
        done_str = Fore.LIGHTCYAN_EX + '█' * int(done) + Style.RESET_ALL
    elif type_of_progress == 3:
        done_str = Fore.LIGHTBLACK_EX + '█' * int(done) + Style.RESET_ALL
    elif type_of_progress == 4:
        done_str = Fore.BLUE + '█' * int(done) + Style.RESET_ALL
    togo_str = '░' * int(PROGRESS_BAR_LEN - done)

    print((f'{title}:' if title else '') + (
        f'[{done_str}{togo_str}] {round(percent_done, 1)}% done  '
        ), end='\r', flush=True)

    if end_with == 100 and round(percent_done) >= end_with:
        sleep(.3)
        print((' '  * (TERMINAL_SIZE-2)),  end='\r', flush=True) # cleanup line

CHCP = 65001
if os.name == 'nt':
    import ctypes
    CHCP = ctypes.windll.kernel32.GetConsoleCP()

def print_encoded(text: str):
    print(text.encode("unicode-escape").decode("latin1") if CHCP != 65001 else text)

def search_resource(path: str, name: str) -> list:
    import glob
    files = glob.glob(os.path.join(path, "**", name), recursive = True)
    return files if len(files) else []

def is_translatable(text: str) -> bool:
    return isinstance(text, str) and len(text.replace('\r','').replace('\n','').strip()) > 0 and '\u25A0' != text

def normalize_n(line: str, into_csv:bool=False) -> str:
    """
    Normalize the newline characters in a string.

    Args:
        line (`str`): The string to be normalized

        into_csv (`bool`):

            If `True`, to Unix-style

            If `False` (default), to Windows-style

    Returns:
        str: normalized string
    """
    if into_csv:
        return line.replace('\r', '')
    else:
        return line.replace('\n', '\r\n')

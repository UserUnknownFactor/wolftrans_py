# -*- coding: utf-8 -*-
import sys, os, glob, re
if sys.version_info < (3, 9): print("This app must run using Python 3.9+"), sys.exit(2)
from wolfrpg import commands, maps, databases, gamedats, common_events, filecoder
from wolfrpg.service_fn import read_csv_list, print_progress
from wolfrpg import yaml_dump

ENABLE_YAML_DUMPING = False

MODE_ALLOW_COMMENTS = False
MODE_REPACK_CE_PARAMS = False
MODE_REPACK_CEBN_PARAMS = False
MODE_REPACK_DB_NAMES = False
MODE_SETSTRING_AS_STRING = True
MODE_CEARG_AS_STRING = True
MODE_REPACK_CE_ARG_N = []
MODE_REPACK_CEBN_ARG_N = []
MODE_REPACK_CE_EVID = []
MODE_REPACK_CEBN_EVID = []

STRINGS_NAME = "strings"
ATTRIBUTES_NAME = "attributes"
STRINGS_DB_POSTFIX = "_" + STRINGS_NAME + ".csv"
ATTRIBUTES_DB_POSTFIX = "_" + ATTRIBUTES_NAME + ".csv"
DEFAULT_OUT_DIR = "translation_out"

import ctypes
CHCP = ctypes.windll.kernel32.GetConsoleCP()

def print_encoded(text):
    print(text.encode("utf-8" if CHCP == 65001 else "unicode-escape"))

def search_resource(path, name):
    files = glob.glob(os.path.join(path, "**", name), recursive = True)
    return files if len(files) else []

def normalize_n(line, into_csv_n = False):
    return line.replace('\r', '') if into_csv_n else line.replace('\n', '\r\n')

def translate_attribute_of_command(command, value) -> bool:
    is_translated = False
    try:
        if isinstance(command, commands.Choices):
            for i, line in enumerate(command.text):
                if (line == value[0] or normalize_n(line, True) == value[0]) and value[1]:
                    command.text[i] = normalize_n(value[1])
                    is_translated = True
        elif isinstance(command, commands.CommonEvent):
            if not MODE_REPACK_CE_PARAMS or MODE_CEARG_AS_STRING: return False
            for i, line in enumerate(command.text):
                if len(MODE_REPACK_CE_ARG_N):
                    for j, evid in enumerate(MODE_REPACK_CE_EVID):
                        if command.args[1] == evid or evid == -1:
                            if i + 1 == MODE_REPACK_CE_ARG_N[j] and (
                                    line == value[0] or normalize_n(line, True) == value[0]) and value[1]:
                                command.text[i] = normalize_n(value[1])
                                is_translated = True
                                break
                elif (line == value[0] or normalize_n(line, True) == value[0]) and value[1]:
                    command.text[i] = normalize_n(value[1])
                    is_translated = True
        elif isinstance(command, commands.CommonEventByName):
            if not MODE_REPACK_CEBN_PARAMS or MODE_CEARG_AS_STRING: return False
            for i, line in enumerate(command.text):
                if len(MODE_REPACK_CEBN_ARG_N):
                    for j, nevid in enumerate(MODE_REPACK_CEBN_EVID):
                        if command.args[1] == nevid or nevid == -1:
                            if i + 1 == MODE_REPACK_CEBN_ARG_N[j] and (
                                    line == value[0] or normalize_n(line, True) == value[0]) and value[1]:
                                command.text[i] = normalize_n(value[1])
                                is_translated = True
                                break
                elif (line == value[0] or normalize_n(line, True) == value[0]) and value[1]:
                    command.text[i] = normalize_n(value[1])
                    is_translated = True
        elif isinstance(command, commands.Database):
            if (command.text and (command.text == value[0] or normalize_n(command.text, True) == value[0])) and value[1]:
                command.text = normalize_n(value[1])
                is_translated = True
            for i, line in enumerate(command.string_args):
                if (command.string_args[i] and (line == value[0] or normalize_n(line, True) == value[0])) and value[1]:
                    command.string_args[i] = normalize_n(value[1])
                    is_translated = True
        elif isinstance(command, commands.StringCondition):
            for i, line in enumerate(command.string_args):
                if (line == value[0] or normalize_n(line, True) == value[0]) and value[1]:
                    command.string_args[i] = normalize_n(value[1])
                    is_translated = True
        elif isinstance(command, commands.Picture):
            if command.ptype == "text":
                if (command.text == value[0] or normalize_n(command.text, True) == value[0]) and value[1]:
                    command.text = normalize_n(value[1])
                    is_translated = True
        elif isinstance(command, commands.SetString):
            if MODE_SETSTRING_AS_STRING: return False
            if (command.text == value[0] or normalize_n(command.text, True) == value[0]) and value[1]:
                command.text = normalize_n(value[1])
                is_translated = True
    except Exception as e:
        print_encoded(command.text)
        raise e
    return is_translated

def translate_string_of_command(command, value) -> bool:
    is_translated = False
    try:
        if isinstance(command, commands.Message):
            if (command.text == value[0] or normalize_n(command.text, True) == value[0]) and value[1]:
                command.text = normalize_n(value[1])
                is_translated = True
        elif isinstance(command, commands.SetString):
            if not MODE_SETSTRING_AS_STRING: return False
            if (command.text == value[0] or normalize_n(command.text, True) == value[0]) and value[1]:
                command.text = normalize_n(value[1])
                is_translated = True
        elif isinstance(command, commands.CommonEvent):
            if not MODE_REPACK_CE_PARAMS or not MODE_CEARG_AS_STRING: return False
            for i, line in enumerate(command.text):
                if len(MODE_REPACK_CE_ARG_N):
                    for j, evid in enumerate(MODE_REPACK_CE_EVID):
                        if command.args[1] == evid or evid == -1:
                            if i + 1 == MODE_REPACK_CE_ARG_N[j] and (
                                    line == value[0] or normalize_n(line, True) == value[0]) and value[1]:
                                command.text[i] = normalize_n(value[1])
                                is_translated = True
                                break
                elif (line == value[0] or normalize_n(line, True) == value[0]) and value[1]:
                    command.text[i] = normalize_n(value[1])
                    is_translated = True
        elif isinstance(command, commands.CommonEventByName):
            if not MODE_REPACK_CEBN_PARAMS or not MODE_CEARG_AS_STRING: return False
            for i, line in enumerate(command.text):
                if len(MODE_REPACK_CEBN_ARG_N):
                    for j, nevid in enumerate(MODE_REPACK_CEBN_EVID):
                        if command.args[1] == nevid or nevid == -1:
                            if i + 1 == MODE_REPACK_CEBN_ARG_N[j] and (
                                    line == value[0] or normalize_n(line, True) == value[0]) and value[1]:
                                command.text[i] = normalize_n(value[1])
                                is_translated = True
                                break
                elif (line == value[0] or normalize_n(line, True) == value[0]) and value[1]:
                    command.text[i] = normalize_n(value[1])
                    is_translated = True
    except Exception as e:
        print_encoded(command.text)
        raise e
    return is_translated

def get_context(command):
    return ''

def make_postfixed_name(name, postfix):
    return os.path.join(os.path.dirname(name), name + postfix)

def remove_ext(name):
    name = name.split('.')
    return '.'.join(name[:-1])

def read_string_translations(name, ext=''):
    name = remove_ext(name)
    name = make_postfixed_name(name, ext + STRINGS_DB_POSTFIX)
    #print_encoded("Parsing " + name)
    return read_csv_list(name)

def read_attribute_translations(name, ext=''):
    name = remove_ext(name)
    name = make_postfixed_name(name, ext + ATTRIBUTES_DB_POSTFIX)
    #print_encoded("Parsing " + name)
    return read_csv_list(name)

def replace_tags(arr, repl_arr):
    if len(arr) == 0:
        return []
    for i in range(len(arr)):
        for trow in repl_arr:
            arr[i][1] = arr[i][1].replace(trow[1], trow[0])
    return arr

def make_dirs(path):
    d = os.path.dirname(path)
    if d != '' and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def make_out_name(name, work_dir):
    new_name = name.replace(work_dir, os.path.join(work_dir, DEFAULT_OUT_DIR))
    make_dirs(new_name)
    return new_name


def main():
    global MODE_SETSTRING_AS_STRING
    global MODE_CEARG_AS_STRING
    global MODE_REPACK_DB_NAMES
    global MODE_REPACK_CE_PARAMS
    global MODE_REPACK_CEBN_PARAMS
    global MODE_ALLOW_COMMENTS

    global MODE_REPACK_CE_ARG_N
    global MODE_REPACK_CEBN_ARG_N
    global MODE_REPACK_CE_EVID
    global MODE_REPACK_CEBN_EVID

    import argparse
    parser = argparse.ArgumentParser()
    #parser.add_argument("-f", default="map,common,game,dbs", help="Types of files to repack (map,common,game,dbs)")
    parser.add_argument("-s", help="Treat SetString as attributes", action="store_false")
    parser.add_argument("-a", help="Treat CommonEvent[ByName] args as attributes", action="store_false")
    parser.add_argument("-n", help="Repack Database names", action="store_true")
    parser.add_argument("-c", help="Don't repack CommonEvent args", action="store_false")
    parser.add_argument("-b", help="Don't repack CommonEventByName args", action="store_false")
    parser.add_argument("-ea", type=str, default='0', metavar="ce_types", nargs='?',
                        help="Comma separated list of allowed CommonEvent args (#|id; ex: 3|12345,5|12345,3|67890)")
    parser.add_argument("-na", type=str, default='0', metavar="cebn_types", nargs='?',
                        help="Comma separated list of allowed CommonEventByName args (#|id; ex: 3|12345,5|12345,3|67890)")
    parser.add_argument("-u", help="Repack strings as UTF-8", action="store_true")
    args = parser.parse_args()
    print(args)

    MODE_SETSTRING_AS_STRING = args.s
    MODE_CEARG_AS_STRING = args.a
    MODE_REPACK_DB_NAMES =  args.n
    MODE_REPACK_CE_PARAMS = args.c
    MODE_REPACK_CEBN_PARAMS = args.b

    MODE_REPACK_CE_ARG_N = [] if not args.ea or args.ea == "0" else args.ea.split(',')
    MODE_REPACK_CE_EVID = [int(i.split('|')[1]) if len(i.split('|'))>1 else -1 for i in MODE_REPACK_CE_ARG_N if len(i.split('|'))>1]
    MODE_REPACK_CE_ARG_N = [int(i.split('|')[0]) for i in MODE_REPACK_CE_ARG_N]
    MODE_REPACK_CEBN_ARG_N = [] if not args.na or args.na == "0" else args.na.split(',')
    MODE_REPACK_CEBN_EVID = [int(i.split('|')[1]) if len(i.split('|'))>1 else -1 for i in MODE_REPACK_CEBN_ARG_N if len(i.split('|'))>1]
    MODE_REPACK_CEBN_ARG_N = [int(i.split('|')[0]) for i in MODE_REPACK_CEBN_ARG_N]

    filecoder.initialize(args.u) # since we detect version == 3 at later stages of decoding we need to specify it beforehand

    work_dir = os.getcwd()

    map_names = list(filter(lambda x: "translation_out" not in x, search_resource(os.getcwd(), "*.mps"))) # map data
    commonevents_name = list(filter(lambda x: "translation_out" not in x, search_resource(os.getcwd(), "CommonEvent.dat"))) # common events
    dat_name = list(filter(lambda x: "translation_out" not in x, search_resource(os.getcwd(), "Game.dat"))) # basicdata
    db_names = list(filter(lambda x: "wolfrpg" not in x and "SysDataBaseBasic" not in x and "translation_out" not in x, search_resource(
        os.getcwd(), "*.project"))) # projects

    #maps_cache = dict()
    print("Translating maps...")
    for map_name in map_names:
        print_encoded(f"Translating {map_name}...")
        try:
            mp = maps.Map(map_name)
        except Exception as e:
            print(f"FAILED: {e}")
            continue
        #maps_cache[map_name] = mp
        strs = read_string_translations(map_name, ".mps")
        attrs = read_attribute_translations(map_name, ".mps")
        tr_b = False
        for event in mp.events:
            for page in event.pages:
                for i, command in enumerate(page.commands):
                    for at in attrs:
                        tr_b |= translate_attribute_of_command(command, at)
                    for j, _s in enumerate(strs):
                        if translate_string_of_command(command, _s):
                            tr_b = True
                            break
        if tr_b:
            mp.write(make_out_name(map_name, work_dir))
        if ENABLE_YAML_DUMPING:
            yaml_dump.dump(mp, remove_ext(map_name))

    print("Translating common events...")
    commonevents_name = commonevents_name[0]
    ce = common_events.CommonEvents(commonevents_name)
    strs = read_string_translations(commonevents_name, ".dat")
    l_strs = len(strs)
    attrs = read_attribute_translations(commonevents_name, ".dat")
    l_attrs = len(attrs)
    print_progress(0, 100)
    l_events = sum(1 for _ in ce.events)
    li = 0
    tr_b = False
    for event in ce.events:
        for i, command in enumerate(event.commands):
            for at in attrs:
                tr_b != translate_attribute_of_command(command, at) # can have many repeating attrs
            for j, _s in enumerate(strs):
                if not _s: continue #in case of db/csv inconsistency we can't just start from the last
                if translate_string_of_command(command, _s):
                    li += 1
                    strs[j] = None # only one translation per string csv, non-repeating
                    tr_b = True
                    print_progress(li / l_strs * 100, 100) #last string should corespond to final event
                    break
    print_progress(100, 100)
    if tr_b:
        ce.write(make_out_name(commonevents_name, work_dir))
    if ENABLE_YAML_DUMPING:
        yaml_dump.dump(ce, remove_ext(commonevents_name))

    print("Translating project databases...")
    for db_name in db_names:
        print("Translating", db_name,"...")
        db_name_only = remove_ext(os.path.basename(db_name))
        if not os.path.isfile(db_name.replace(".project", ".dat")):
            print("No .dat file for", db_name)
            continue
        try:
            db = databases.Database(db_name, os.path.join(os.path.dirname(db_name),  db_name_only + ".dat"))
        except Exception as e:
            print("Skipping", db_name, "due to error:\n", e,"\n")
            continue
        attrs = read_attribute_translations(db_name, ".dat")
        for t in db.types:
            for i, d in enumerate(t.data):
                if MODE_REPACK_DB_NAMES and hasattr(d, "name"):
                    for at in attrs:
                        if (d.name == at[0] or normalize_n(d.name, True) == at[0]) and at[1]:
                            #print(t.data[i], d.name, at[1])
                            t.data[i].name = at[1].replace('\r', '').replace('\n', '\r\n')
                for j, l in enumerate(d.each_translatable()):
                    for at in attrs:
                        if (l[0] == at[0] or normalize_n(l[0], True) == at[0]) and at[1]:
                            #print(t.data[i], l[0], at[1])
                            t.data[i].set_field(l[1], at[1].replace('\r', '').replace('\n', '\r\n'))
        out_name = make_out_name(db_name, work_dir)
        db.write(out_name, remove_ext(out_name) + '.dat')
        if ENABLE_YAML_DUMPING:
            yaml_dump.dump(db, remove_ext(db_name))

    dat_name = dat_name[0]
    attrs = [] #read_attribute_translations(dat_name, ".dat")
    if len(attrs):
        print("Translating game dat file...")
        gd = gamedats.GameDat(dat_name)
        for a in attrs:
            if gd.title and gd.title == a[0] and a[1]:
                gd.title = a[1]
            if gd.version and gd.version == a[0] and a[1]:
                gd.version = a[1]
            if gd.font and gd.font == a[0] and a[1]:
                gd.font = a[1]
            if gd.subfonts:
                for i, font in enumerate(gd.subfonts):
                    if font == a[0] and a[1]:
                        gd.subfonts[i] = a[1]
        gd.write(make_out_name(dat_name, work_dir))

if __name__ == "__main__":
    main()
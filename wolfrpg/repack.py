# -*- coding: utf-8 -*-
import sys, os
if sys.version_info < (3, 9): print("This app must run using Python 3.9+"), sys.exit(2)
from wolfrpg import commands, maps, databases, gamedats, common_events, filecoder
from wolfrpg import yaml_dump
from wolfrpg.service_fn import *
from wolfrpg.simple_trie import *

DROP_EMTPY = False
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
COMMENT_TAG = "//"

def is_string_command(command):
    return isinstance(command, (commands.Message, commands.SetString)) or \
           (isinstance(command, commands.CommonEvent) and MODE_REPACK_CE_PARAMS and MODE_CEARG_AS_STRING) or \
           (isinstance(command, commands.CommonEventByName) and MODE_REPACK_CEBN_PARAMS and MODE_CEARG_AS_STRING)

def is_attribute_command(command):
    return isinstance(command, (commands.Choices, commands.StringCondition, commands.Picture,
                                commands.Database)) or \
           (isinstance(command, commands.CommonEvent) and MODE_REPACK_CE_PARAMS and not MODE_CEARG_AS_STRING) or \
           (isinstance(command, commands.CommonEventByName) and MODE_REPACK_CEBN_PARAMS and not MODE_CEARG_AS_STRING) or \
           (isinstance(command, commands.SetString) and not MODE_SETSTRING_AS_STRING)

def build_ce_trie(ce):
    trie = Trie()
    for event_index, event in enumerate(ce.events):
        for command_index, command in enumerate(event.commands):
            if command._has_text:
                for line_index, line in enumerate(command.string_args):
                    if command.is_text_line(line_index):
                        trie.insert(line, type(command).__name__, (event_index, command_index), line_index)
    return trie


def build_map_trie(mp):
    trie = Trie()
    for event_index, event in enumerate(mp.events):
        for page_index, page in enumerate(event.pages):
            for command_index, command in enumerate(page.commands):
                if command._has_text:
                    for line_index, line in enumerate(command.string_args):
                        if command.is_text_line(line_index):
                            trie.insert(line, type(command).__name__, (event_index, page_index, command_index), line_index)
    return trie

def apply_translations(target, strs, attrs, trie):
    ret_translated = False
    len_strs = len(strs)
    len_attrs = len(attrs)
    total_translations = len_strs + len_attrs
    processed_translations = 0

    def process_command(command, original, translated, line_index, is_string):
        nonlocal processed_translations
        is_translated = False
        if not DROP_EMTPY and not translated: return False
        if is_string:
            if not is_string_command(command): return False
        else:
            if not is_attribute_command(command): return False

        if isinstance(command, (
                commands.Message, commands.Picture,
                commands.Choices, commands.SetString,
                commands.StringCondition, commands.Database)):
            # NOTE: SetString can have several string_args
            if not isinstance(command.text, str):
                for i, line in enumerate(command.text):
                    if normalize_n(line, True) == original:
                        command.text[i] = normalize_n(translated)
                        is_translated = True
                        break
            else:
                if normalize_n(command.text, True) == original:
                    command.text = normalize_n(translated)
                    is_translated = True
        elif isinstance(command, commands.CommonEvent):
            for i, line in enumerate(command.string_args):
                if len(MODE_REPACK_CE_ARG_N):
                    for j, evid in enumerate(MODE_REPACK_CE_EVID):
                        if command.args[1] == evid or evid == -1:
                            if i + 1 == MODE_REPACK_CE_ARG_N[j] and normalize_n(line, True) == original:
                                command.string_args[i] = normalize_n(translated)
                                is_translated = True
                                break
                elif normalize_n(line, True) == original:
                    command.text[i] = normalize_n(translated)
                    is_translated = True
        elif isinstance(command, commands.CommonEventByName):
            for i, line in enumerate(command.string_args):
                if len(MODE_REPACK_CEBN_ARG_N):
                    for j, nevid in enumerate(MODE_REPACK_CEBN_EVID):
                        if command.args[1] == nevid or nevid == -1:
                            if i + 1 == MODE_REPACK_CEBN_ARG_N[j] and normalize_n(line, True) == original:
                                command.string_args[i] = normalize_n(translated)
                                is_translated = True
                                break
                elif normalize_n(line, True) == original:
                    command.string_args[i] = normalize_n(translated)
                    is_translated = True

        return is_translated

    for string_pair in strs:
        try:
            source_string, translated_string = string_pair
        except:
            print(f"corrupted line {string_pair} (check ¶ newline escapes)")
            continue
        node = trie.search(source_string)
        if node:
            coords_to_delete = []
            for coord_i, coordinate in enumerate(node.coordinates):
                if len(coordinate) == 3:  # Map events
                    event_index, page_index, command_index = coordinate
                    command = target.events[event_index].pages[page_index].commands[command_index]
                else:  # Common events
                    event_index, command_index = coordinate
                    command = target.events[event_index].commands[command_index]

                tr_s = process_command(command, source_string, translated_string, node.line_indexes[coord_i], True)
                ret_translated |= tr_s

                if tr_s:
                    coords_to_delete.append(coord_i)
                    break
            for i in sorted(coords_to_delete, reverse=True):
                del node.coordinates[i]

        processed_translations += 1
        print_progress(processed_translations / total_translations * 100, 100)

    for source_attribute, translated_string in attrs.items():
        node = trie.search(source_attribute)
        if node:
            for coordinate in node.coordinates:
                if len(coordinate) == 3:
                    event_index, page_index, command_index = coordinate
                    command = target.events[event_index].pages[page_index].commands[command_index]
                else:
                    event_index, command_index = coordinate
                    command = target.events[event_index].commands[command_index]

                ret_translated |= process_command(command, source_attribute, translated_string, None, False)

        processed_translations += 1
        print_progress(processed_translations / total_translations * 100, 100)

    return ret_translated

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
    #print("Parsing " + name)
    return [line for line in read_csv_list(name) if line[0][:len(COMMENT_TAG)] != COMMENT_TAG]

def read_attribute_translations(name, ext=''):
    name = remove_ext(name)
    name = make_postfixed_name(name, ext + ATTRIBUTES_DB_POSTFIX)
    #print("Parsing " + name)
    ret = {}
    for line in read_csv_list(name):
        if line[0][:len(COMMENT_TAG)] == COMMENT_TAG: continue
        try:
            ret.update({line[0]: line[1]})
            ret.update({normalize_n(line[0]): line[1]})
        except Exception as e:
            print(line, e)
    return ret

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

    global DEFAULT_OUT_DIR

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", default="maps,common,game,dbs", help="Types of files to repack (maps,common,game,dbs)")
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
    parser.add_argument("-out", default=DEFAULT_OUT_DIR, help="Output directory")
    args = parser.parse_args()
    print(args)

    if os.path.isdir(args.out):
        DEFAULT_OUT_DIR = args.out
    print(f"Output directory: {os.path.abspath(args.out)}")

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

    MODE_BREAK_ON_EXCEPTIONS = False

    filecoder.initialize(args.u) # since we detect version == 3 at later stages of decoding we need to specify it beforehand

    work_dir = os.getcwd()

    map_names = list(filter(lambda x: "translation_out" not in x, search_resource(os.getcwd(), "*.mps"))) if "maps" in args.f else []  # map data
    commonevents_name = list(filter(lambda x: "translation_out" not in x, search_resource(os.getcwd(), "CommonEvent.dat"))) if "common" in args.f else []  # common events
    dat_name = list(filter(lambda x: "translation_out" not in x, search_resource(os.getcwd(), "Game.dat"))) if "game" in args.f else []  # basicdata
    db_names = list(filter(lambda x: "wolfrpg" not in x and "SysDataBaseBasic" not in x and "translation_out" not in x, search_resource(
        os.getcwd(), "*.project"))) if "dbs" in args.f else []  # projects


    #maps_cache = dict()
    if map_names:
        print("Translating maps...")
    for map_name in map_names:
        strs = read_string_translations(map_name, ".mps")
        attrs = read_attribute_translations(map_name, ".mps")
        if not strs and not attrs: continue
        print(f"Translating map {os.path.relpath(map_name)}...")
        if MODE_BREAK_ON_EXCEPTIONS:
            mp = maps.Map(map_name)
        else:
            try:
                mp = maps.Map(map_name)
            except Exception as e:
                print(f"FAILED: {e}")
                continue
        #maps_cache[map_name] = mp
        if strs or attrs:
            map_trie = build_map_trie(mp)
            is_translated = apply_translations(mp, strs, attrs, map_trie)
            if is_translated:
                mp.write(make_out_name(map_name, work_dir))
            if ENABLE_YAML_DUMPING:
                yaml_dump.dump(mp, remove_ext(map_name))


    if commonevents_name:
        commonevents_name = commonevents_name[0]
        strs = read_string_translations(commonevents_name, ".dat")
        attrs = read_attribute_translations(commonevents_name, ".dat")
        if strs or attrs:
            print(f"Translating common events {os.path.relpath(commonevents_name)}...")
            if MODE_BREAK_ON_EXCEPTIONS:
                ce = common_events.CommonEvents(commonevents_name)
            else:
                try:
                    ce = common_events.CommonEvents(commonevents_name)
                except Exception as e:
                    print(f"FAILED: {e}")
                    sys.exit(1)
            print_progress(0, 100)
            ce_trie = build_ce_trie(ce)
            is_translated = apply_translations(ce, strs, attrs, ce_trie)
            print_progress(100, 100)
            if is_translated:
                ce.write(make_out_name(commonevents_name, work_dir))
            if ENABLE_YAML_DUMPING:
                yaml_dump.dump(ce, remove_ext(commonevents_name))

    if db_names:
        print("Translating project databases...")
    for db_name in db_names:
        attrs = read_attribute_translations(db_name, ".dat")
        if not attrs: continue
        print(f"Translating database {os.path.relpath(db_name)}...")
        db_name_only = remove_ext(os.path.basename(db_name))
        if not os.path.isfile(db_name.replace(".project", ".dat")):
            print("No .dat file for", db_name)
            continue
        if MODE_BREAK_ON_EXCEPTIONS:
            db = databases.Database(db_name, os.path.join(os.path.dirname(db_name),  db_name_only + ".dat"))
        else:
            try:
                db = databases.Database(db_name, os.path.join(os.path.dirname(db_name),  db_name_only + ".dat"))
            except Exception as e:
                print("Skipping", db_name, "due to error:\n", e,"\n")
                continue
        for t in db.types:
            for i, d in enumerate(t.data):
                if MODE_REPACK_DB_NAMES and hasattr(d, "name"):
                    if d.name in attrs and attrs[d.name]:
                        #print(t.data[i], d.name, at[1])
                        t.data[i].name =  attrs[d.name].replace('\r', '').replace('\n', '\r\n')
                for j, l in enumerate(d.each_translatable()):
                    if l[0] in attrs and attrs[l[0]]:
                        #print(t.data[i], l[0], at[1])
                        t.data[i].set_field(l[1],  attrs[l[0]].replace('\r', '').replace('\n', '\r\n'))
        out_name = make_out_name(db_name, work_dir)
        db.write(out_name, remove_ext(out_name) + '.dat')
        if ENABLE_YAML_DUMPING:
            yaml_dump.dump(db, remove_ext(db_name))

    if dat_name:
        dat_name = dat_name[0]
        strs = read_string_translations(dat_name, ".dat")
        if strs:
            print(f"Translating game database {os.path.relpath(dat_name)}...")
            if MODE_BREAK_ON_EXCEPTIONS:
                gd = gamedats.GameDat(dat_name)
            else:
                try:
                    gd = gamedats.GameDat(dat_name)
                except Exception as e:
                    print("Skipping", db_name, "due to error:\n", e,"\n")
                    sys.exit(1)

            gds = gd.string_settings
            for line in strs:
                if len(line) <3: continue
                if not line[1] and not DROP_EMTPY: continue
                if line[2] == "TITLE":
                    gds.title = line[1]
                elif line[2] == "VERSION":
                    gds.version = line[1]
                elif line[2] == "FONT":
                    gds.font = line[1]
                else:
                    for i, font in enumerate(gds.subfonts):
                        if line[2] == f"SUBFONT{i}":
                            gds.subfonts[i] = line[1]
                            break
            gd.write(make_out_name(dat_name, work_dir))

if __name__ == "__main__":
    main()
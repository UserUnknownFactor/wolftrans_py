# -*- coding: utf-8 -*-
import sys, os, glob, re
if sys.version_info < (3, 9): print("This app must run using Python 3.9+"), sys.exit(2)
from wolfrpg import commands, maps, databases, gamedats, common_events, filecoder
from wolfrpg.service_fn import write_csv_list, read_csv_dict, normalize_n, is_translatable
from wolfrpg.wenums import EncodingType
from wolfrpg import  yaml_dump
import hashlib

ENABLE_YAML_DUMPING = True
MODE_BREAK_ON_EXCEPTIONS = False

MODE_SETSTRING_AS_STRING = False
MODE_CEARG_AS_STRING = False
MODE_EXTRACT_COMMENTS = False
MODE_EXTRACT_DB_NAMES = True
MODE_EXTRACT_CE = False
MODE_EXTRACT_CE_BY_NAME = False
MODE_EXTRACT_DATABASE_REFS = False
MODE_EXTRACT_CE_ARG_N = list()
MODE_EXTRACT_CEBN_ARG_N = list()
MODE_EXTRACT_CE_EVID = list()
MODE_EXTRACT_CEBN_EVID = list()

STRINGS_NAME = "strings"
ATTRIBUTES_NAME = "attributes"
STRINGS_DB_POSTFIX = "_" + STRINGS_NAME + ".csv"
ATTRIBUTES_DB_POSTFIX = "_" + ATTRIBUTES_NAME + ".csv"
REPLACEMENT_TAGS_RE = r'(?:「|」|[@]\d+\n|(?:(?:\\[-\+_\.\{\}%A-Za-z\d]+\[[\d:-_]+\]){1,}|\\[A-Za-z\d<>]+))'
MEDIA_EXTENSION_RE = re.compile(r'\.(?:png|wave?|aac|jpe?g|ogg|mp3|flac|webp)$')


def tag_hash(string, str_enc="utf-8", hash_len=7):
    """ Generates short English tags for MTL from any kind of string. """
    if len(string) < 1: return ''
    d = hashlib.sha1(string.encode(str_enc)).digest()
    s = ''
    n_chars = 26 + 10
    for i in range(0, hash_len):
        x = d[i] % n_chars
        #s += chr(ord('a') + x) # lowercase letters, n_chars = 26
        s += (chr(ord('0') + x - 26) if x >= 26 else chr(ord('a') + x)) # numbers + lowercase, n_chars = 36
        #s += (chr(ord('A') + x - 26) if x >= 26 else chr(ord('a') + x)) # letters, n_chars = 52
    return s

def search_resource(path, name):
    files = glob.glob(os.path.join(path, "**", name), recursive = True)
    return files if len(files) else []

def extract_previous(filename, textarr):
    old = read_csv_dict(filename.replace(".csv", ".old"))
    commented = {}
    for k, v in old.items():
        if k.startswith('//'):
            commented[k[2:]] = v
    if not len(old): return
    for i, a in enumerate(textarr):
        if a[0] in commented:
            textarr[i][1] = commented[a[0]]
            textarr[i][0] = '//' + a[0]
        elif a[0] in old:
            textarr[i][1] = old[a[0]]
    return textarr

def normalize_and_filter(text):
    if isinstance(text, str):
        return [normalize_n(text, True)] if is_translatable(text) else []
    if isinstance(text, list):
        return [normalize_n(i, True) for i in text if is_translatable(i)]
    return []

def attributes_of_command(command):
    if isinstance(command, commands.Choices):
        return normalize_and_filter(command.text)
    elif isinstance(command, commands.CommonEvent):
        if not MODE_CEARG_AS_STRING and MODE_EXTRACT_CE:
            return normalize_and_filter(command.text)
    elif isinstance(command, commands.CommonEventByName):
        if not MODE_CEARG_AS_STRING and MODE_EXTRACT_CE_BY_NAME:
            return normalize_and_filter(command.text)
    elif isinstance(command, commands.Database):
        if MODE_EXTRACT_DATABASE_REFS:
            return normalize_and_filter(command.text)
    elif isinstance(command, commands.StringCondition):
        return normalize_and_filter(command.text)
    elif isinstance(command, commands.Picture):
        if command.ptype == 'text':
            return normalize_and_filter(command.text)
    elif isinstance(command, commands.SetString):
        if not MODE_SETSTRING_AS_STRING:
            return normalize_and_filter(command.text)
    return []

def strings_of_command(command):
    if isinstance(command, commands.Message):
        return normalize_and_filter(command.text)
    elif isinstance(command, commands.Comment):
        if MODE_EXTRACT_COMMENTS:
            return normalize_and_filter(command.text)
    elif isinstance(command, commands.SetString):
        if MODE_SETSTRING_AS_STRING:
            return normalize_and_filter(command.text)
    elif isinstance(command, commands.CommonEvent):
        if MODE_CEARG_AS_STRING and MODE_EXTRACT_CE:
            return normalize_and_filter(command.text)
    elif isinstance(command, commands.CommonEventByName):
        if MODE_CEARG_AS_STRING and MODE_EXTRACT_CE_BY_NAME:
            return normalize_and_filter(command.text)
    return []

def get_context(command):
    return ''

def make_csv_field(text, context, translation=''):
    return [text, translation]#, get_context(command)]

def make_postfixed_name(name, postfix, ext=''):
    name = remove_ext(name)
    return os.path.join(os.path.dirname(name), name + ext + postfix)

def remove_ext(name):
    name = name.split('.')
    return '.'.join(name[:-1])

def write_translations(name, attrs, strs, ext=''):
    extract_previous(make_postfixed_name(name, ATTRIBUTES_DB_POSTFIX, ext), attrs)
    write_csv_list(make_postfixed_name(name, ATTRIBUTES_DB_POSTFIX, ext), attrs)
    extract_previous(make_postfixed_name(name, STRINGS_DB_POSTFIX, ext), strs)
    write_csv_list(make_postfixed_name(name, STRINGS_DB_POSTFIX, ext), strs)

def search_tags(arr, re_tags=REPLACEMENT_TAGS_RE):
    if len(arr) == 0:
        return []
    re_tags_c = re.compile(re_tags)
    tags = set()
    for row in arr:
        t = set(re_tags_c.findall(row[0]))
        if len(t):
            tags = tags.union(t)
    return list(tags)


def main():
    global MODE_SETSTRING_AS_STRING
    global MODE_CEARG_AS_STRING
    global MODE_EXTRACT_DB_NAMES
    global MODE_EXTRACT_CE
    global MODE_EXTRACT_CE_BY_NAME
    global MODE_EXTRACT_DATABASE_REFS
    global MODE_EXTRACT_COMMENTS

    global MODE_EXTRACT_CE_ARG_N
    global MODE_EXTRACT_CEBN_ARG_N
    global MODE_EXTRACT_CE_EVID
    global MODE_EXTRACT_CEBN_EVID

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", default="maps,common,game,dbs", help="Type of files to extract (maps,common,game,dbs)")
    parser.add_argument("-s", help="Treat SetString as attributes", action="store_false")
    parser.add_argument("-a", help="Treat CommonEvent[ByName] args as attributes", action="store_false")
    parser.add_argument("-n", help="Don't extract Database names", action="store_false")
    parser.add_argument("-c", help="Don't extract CommonEvent args", action="store_false")
    parser.add_argument("-b", help="Don't extract CommonEventByName args", action="store_false")
    parser.add_argument("-d", help="Don't extract Database refs", action="store_false")
    parser.add_argument("-u", help="Extract strings as UTF-8", action="store_true")
    #parser.add_argument("-ea", type="str", default='0', metavar="ce_types", nargs='?',
    #                    help="List of allowed CommonEvent args (#|id; ex: 3|12345,5|12345,3|67890); default: all")
    #parser.add_argument("-na", type="str", default='0', metavar="cebn_types", nargs='?',
    #                    help="List of allowed CommonEventByName args (#|id; ex: 3|12345,5|12345,3|67890); default: all")
    args = parser.parse_args()
    print(args)

    MODE_SETSTRING_AS_STRING = args.s
    MODE_CEARG_AS_STRING = args.a
    MODE_EXTRACT_DB_NAMES =  args.n
    MODE_EXTRACT_CE = args.c
    MODE_EXTRACT_CE_BY_NAME =  args.b
    MODE_EXTRACT_DATABASE_REFS = args.d

    """
    MODE_EXTRACT_CE_ARG_N = [] if not args.ea or args.ea == "0" else args.ea.split(',')
    MODE_EXTRACT_CE_EVID = [int(i.split('|')[1]) if len(i.split('|'))>1 else -1 for i in MODE_EXTRACT_CE_ARG_N if len(i.split('|'))>1]
    MODE_EXTRACT_CE_ARG_N = [int(i.split('|')[0]) for i in MODE_EXTRACT_CE_ARG_N]
    MODE_EXTRACT_CEBN_ARG_N = [] if not args.na or args.na == "0" else args.na.split(',')
    MODE_EXTRACT_CEBN_EVID = [int(i.split('|')[1]) if len(i.split('|'))>1 else -1 for i in MODE_EXTRACT_CEBN_ARG_N if len(i.split('|'))>1]
    MODE_EXTRACT_CEBN_ARG_N = [int(i.split('|')[0]) for i in MODE_EXTRACT_CEBN_ARG_N]
    """

    #filecoder.initialize(args.u) # since we may detect version 3 at later stages of decoding we need to specify it beforehand

    map_names = search_resource(os.getcwd(), "*.mps") if "maps" in args.f else [] # map data
    commonevents_name = search_resource(os.getcwd(), "CommonEvent.dat") if "common" in args.f else [] # common events
    dat_name = search_resource(os.getcwd(), "Game.dat") if "game" in args.f else []  # basic data
    db_names = list(filter(lambda x: "wolfrpg" not in x and "SysDataBaseBasic" not in x, search_resource(
        os.getcwd(), "*.project"))) if "dbs" in args.f else [] # projects

    tags = []

    if dat_name: 
        dat_name = dat_name[0]
        gamedat_failed = None
        if MODE_BREAK_ON_EXCEPTIONS:
            gd = gamedats.GameDat(dat_name)
        else:
            try:
                gd = gamedats.GameDat(dat_name)
            except Exception as e:
                gamedat_failed = e
        if gamedat_failed is None:
            filecoder.initialize(gd.encoding_type == EncodingType.UNICODE)
            if not os.path.isfile(make_postfixed_name(dat_name, STRINGS_DB_POSTFIX, ".dat")):
                print("Extracting",os.path.basename(dat_name) +"...")
                translatable = []
                gds = gd.string_settings
                if gds.title: translatable.append([gds.title, '', "TITLE"])
                if gds.version: translatable.append([gds.version, '', "VERSION"])
                if gds.font: translatable.append([gds.font, '', "FONT"])
                if gds.subfonts: 
                    translatable += [[font, '', f"SUBFONT{i}"] for i, font in enumerate(gds.subfonts)]
                dat_name_only = remove_ext(os.path.basename(dat_name))
                extract_previous(os.path.join(
                    os.path.dirname(dat_name),
                    dat_name_only + ".dat" + ATTRIBUTES_DB_POSTFIX), translatable)
                write_csv_list(os.path.join(
                    os.path.dirname(dat_name),
                    dat_name_only + ".dat" + ATTRIBUTES_DB_POSTFIX), translatable)
        if gamedat_failed:
            print(f"FAILED: {gamedat_failed}")
    else:
        filecoder.initialize(args.u)

    #maps_cache = dict()
    #map_names = []
    for map_name in map_names:
        if os.path.isfile(
            make_postfixed_name(map_name, ATTRIBUTES_DB_POSTFIX, ".mps")) or os.path.isfile(
            make_postfixed_name(map_name, STRINGS_DB_POSTFIX, ".mps")):
            continue
        print("Extracting",os.path.basename(map_name) +"...")
        translatable_attrs = dict()
        translatable_strings = []
        if MODE_BREAK_ON_EXCEPTIONS:
            mp = maps.Map(map_name)
        else:
            try:
                mp = maps.Map(map_name)
            except Exception as e:
                print(f"FAILED: {e}")
                continue
        #maps_cache[map_name] = mp
        for event in mp.events:
            for page in event.pages:
                for i, command in enumerate(page.commands):
                    a = dict.fromkeys(attributes_of_command(command))
                    if len(a):
                        translatable_attrs = translatable_attrs | a
                    s = strings_of_command(command)
                    if not s: continue
                    translatable_strings += [make_csv_field(
                        strn, command) for strn in s if not MEDIA_EXTENSION_RE.search(strn)]
        translatable_attrs = [make_csv_field(attr, command) for attr in translatable_attrs]
        write_translations(map_name, translatable_attrs, translatable_strings, ".mps")
        tags += search_tags(translatable_attrs)
        tags += search_tags(translatable_strings)
        if ENABLE_YAML_DUMPING:
            yaml_dump.dump(mp, remove_ext(map_name))

    if len(commonevents_name): commonevents_name = commonevents_name[0]
    if len(commonevents_name) and not (
            os.path.isfile(make_postfixed_name(commonevents_name, ATTRIBUTES_DB_POSTFIX, ".dat")) or (
                os.path.isfile(make_postfixed_name(commonevents_name, STRINGS_DB_POSTFIX, ".dat")))):
        print("Extracting",os.path.basename(commonevents_name) +"...")
        if MODE_BREAK_ON_EXCEPTIONS:
            ce = common_events.CommonEvents(commonevents_name)
        else:
            try:
                ce = common_events.CommonEvents(commonevents_name)
            except Exception as e:
                print(e)
                sys.exit(2)
        translatable_attrs = dict()
        translatable_strings = []
        for event in ce.events:
            for i, command in enumerate(event.commands):
                a = dict.fromkeys(attributes_of_command(command))
                if len(a):
                    translatable_attrs = translatable_attrs | a
                s = strings_of_command(command)
                if not s: continue
                translatable_strings += [make_csv_field(
                    strn, command) for strn in s if not MEDIA_EXTENSION_RE.search(strn)]
        translatable_attrs = [make_csv_field(attr, command) for attr in translatable_attrs]
        write_translations(commonevents_name, translatable_attrs, translatable_strings, ".dat")
        tags += search_tags(translatable_attrs)
        tags += search_tags(translatable_strings)
        if ENABLE_YAML_DUMPING:
            yaml_dump.dump(ce, remove_ext(commonevents_name))

    for db_name in db_names:
        if os.path.isfile(make_postfixed_name(db_name, ATTRIBUTES_DB_POSTFIX, ".dat")):
            continue
        base_name = os.path.basename(db_name)
        print("Extracting", base_name + "...")
        db_name_only = remove_ext(os.path.basename(db_name))
        if MODE_BREAK_ON_EXCEPTIONS:
            db = databases.Database(db_name, os.path.join(os.path.dirname(db_name),  db_name_only + ".dat"))
        else:
            try:
                db = databases.Database(db_name, os.path.join(os.path.dirname(db_name),  db_name_only + ".dat"))
            except Exception as e:
                print(e)
                continue
        translatable = []
        test_a = set()
        for t in db.types:
            for i, d in enumerate(t.data):
                if MODE_EXTRACT_DB_NAMES and d.name and d.name not in test_a:
                    item = d.name.replace('\r', '')
                    if item.replace('\r','').replace('\n','').strip():
                        translatable.append([item, ''])
                        test_a.add(d.name)
                for l in d.each_translatable():
                    if len(l) and len(l[0]):
                        item = l[0].replace('\r', '')
                        if item not in test_a:
                            translatable.append([item, ''])#, f"DATABASE@{t.data.index}"])
                            test_a.add(item)

        extract_previous(os.path.join(
            os.path.dirname(db_name),
            db_name_only + ".dat" + ATTRIBUTES_DB_POSTFIX), translatable)
        write_csv_list(os.path.join(
            os.path.dirname(db_name),
            db_name_only + ".dat" + ATTRIBUTES_DB_POSTFIX), translatable)
        tags += search_tags(translatable)
        if ENABLE_YAML_DUMPING:
            yaml_dump.dump(db, remove_ext(db_name))

    tags = [[t, f"{tag_hash(t)};"] for i, t in enumerate(set(tags))]
    tags = sorted(tags, reverse=True, key=lambda x: len(x[0]))
    write_csv_list(os.path.join(os.getcwd(), "replacement_tags.csv"), tags)

if __name__ == "__main__":
    main()
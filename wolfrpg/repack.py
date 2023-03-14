# -*- coding: utf-8 -*-
import sys, os, glob, re
from wolfrpg import commands, maps, databases, gamedats, common_events
from wolfrpg.service_fn import read_csv_list, print_progress
#from ruamel import yaml # NOTE: for debug and string search purposes

MODE_SETSTRING_AS_STRING = any(a == "-s" for a in sys.argv[1:]) #True
MODE_ENABLE_CE_PARAMS = True

STRINGS_NAME = "strings"
ATTRIBUTES_NAME = "attributes"
STRINGS_DB_POSTFIX = "_" + STRINGS_NAME + ".csv"
ATTRIBUTES_DB_POSTFIX = "_" + ATTRIBUTES_NAME + ".csv"
DEFAULT_OUT_DIR = "translation_out"

def search_resource(path, name):
    files = glob.glob(os.path.join(path, "**", name), recursive = True)
    return files if len(files) else []
    
def normalize_n(line, into_csv_n = False):
    return line.replace('\r\n', '\n') if into_csv_n else line.replace('\n', '\r\n')

def translate_attribute_of_command(command, value):
    is_translated = False
    if isinstance(command, commands.Choices):
        for i, line in enumerate(command.text):
            if (line == value[0] or normalize_n(line, True) == value[0]) and value[1]:
                command.text[i] = normalize_n(value[1])
                is_translated = True
    elif MODE_ENABLE_CE_PARAMS and isinstance(command, commands.CommonEvent):
        for i, line in enumerate(command.text):
            if (line == value[0] or normalize_n(line, True) == value[0]) and value[1]:
                command.text[i] = normalize_n(value[1])
                is_translated = True
    elif MODE_ENABLE_CE_PARAMS and isinstance(command, commands.CommonEventByName):
        for i, line in enumerate(command.text):
            if (line == value[0] or normalize_n(line, True) == value[0]) and value[1]:
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
        if command.ptype == 'text':
            if (command.text == value[0] or normalize_n(command.text, True) == value[0]) and value[1]:
                command.text = normalize_n(value[1])
                is_translated = True
    elif not MODE_SETSTRING_AS_STRING and isinstance(command, commands.SetString):
        if (command.text == value[0] or normalize_n(command.text, True) == value[0]) and value[1]:
            command.text = normalize_n(value[1])
            is_translated = True
    return is_translated

def translate_string_of_command(command, value):
    is_translated = False
    if isinstance(command, commands.Message):
        if (command.text == value[0] or normalize_n(command.text, True) == value[0]) and value[1]:
            command.text = normalize_n(value[1])
            is_translated = True
    elif MODE_SETSTRING_AS_STRING and isinstance(command, commands.SetString):
        if (command.text == value[0] or normalize_n(command.text, True) == value[0]) and value[1]:
            command.text = normalize_n(value[1])
            is_translated = True
    return is_translated

def get_context(command):
    return ''

def make_postfixed_name(name, postfix):
    return os.path.join(os.path.dirname(name), name + postfix)

def remove_ext(name):
    name = name.split('.')
    return '.'.join(name[:-1])

def read_string_translations(name):
    name = remove_ext(name)
    return read_csv_list(make_postfixed_name(name, STRINGS_DB_POSTFIX))

def read_attribute_translations(name):
    name = remove_ext(name)
    return read_csv_list(make_postfixed_name(name, ATTRIBUTES_DB_POSTFIX))

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
    work_dir = os.getcwd()

    map_names = list(filter(lambda x: "translation_out" not in x, search_resource(os.getcwd(), '*.mps'))) # map data
    commonevents_name = list(filter(lambda x: "translation_out" not in x, search_resource(os.getcwd(), 'CommonEvent.dat'))) # common events
    dat_name = list(filter(lambda x: "translation_out" not in x, search_resource(os.getcwd(), 'Game.dat'))) # basicdata
    db_names = list(filter(lambda x: "wolfrpg" not in x and "SysDataBaseBasic" not in x and "translation_out" not in x, search_resource(
        os.getcwd(), '*.project'))) # projects

    #maps_cache = dict()
    print("Translating maps...")
    for map_name in map_names:
        print("Translating",map_name,"...")
        try:
            mp = maps.Map(map_name)
        except Exception as e:
            print(f'FAILED\n{e}')
            continue
        #maps_cache[map_name] = mp
        strs = read_string_translations(map_name)
        attrs = read_attribute_translations(map_name)
        for event in mp.events:
            for page in event.pages:
                for i, command in enumerate(page.commands):
                    for at in attrs:
                        translate_attribute_of_command(command, at)
                    tr_b = False
                    for j, _s in enumerate(strs):
                        if translate_string_of_command(command, _s):
                            tr_b = True
                            break

        mp.write(make_out_name(map_name, work_dir))
        #with open(remove_ext(map_name) + '.yaml') as f: w.write(yaml.dump(mp))

    print("Translating common events...")
    commonevents_name = commonevents_name[0]
    ce = common_events.CommonEvents(commonevents_name)
    strs = read_string_translations(commonevents_name)
    l_strs = len(strs)
    attrs = read_attribute_translations(commonevents_name)
    l_attrs = len(attrs)
    print_progress(0, 100)
    l_events = sum(1 for _ in ce.events)
    li = 0
    for event in ce.events:
        for i, command in enumerate(event.commands):
            for at in attrs:
                translate_attribute_of_command(command, at) # can have many repeating attrs
            tr_b = False
            for j, _s in enumerate(strs):
                if not _s: continue #in case of db/csv inconsistency we can't just start from the last
                if translate_string_of_command(command, _s):
                    li += 1
                    strs[j] = None # only one translation per string csv, non-repeating
                    tr_b = True
                    print_progress(li / l_strs * 100, 100) #last string should corespond to final event
                    break
    print_progress(100, 100)
    ce.write(make_out_name(commonevents_name, work_dir))
    #with open(remove_ext(commonevents_name) + '.yaml') as f: w.write(yaml.dump(ce))

    print("Translating project databases...")
    for db_name in db_names:
        print("Translating",db_name,"...")
        db_name_only = remove_ext(os.path.basename(db_name))
        db = databases.Database(db_name, os.path.join(os.path.dirname(db_name),  db_name_only + ".dat"))
        attrs = read_attribute_translations(db_name)
        for t in  db.types:
            for i, d in enumerate(t.data):
                for j, l in enumerate(d.each_translatable()):
                    for at in attrs:
                        if (l[0] == at[0] or normalize_n(l[0], True) == at[0]) and at[1]:
                            #print(t.data[i], l[0], at[1])
                            t.data[i].set_field(l[1], at[1].replace('\r\n', '\n').replace('\n','\r\n'))
        out_name = make_out_name(db_name, work_dir)
        db.write(out_name, remove_ext(out_name) + '.dat')
        #with open(remove_ext(db_name) + '.yaml') as f: w.write(yaml.dump(db))

    dat_name = dat_name[0]
    attrs = [] #read_attribute_translations(dat_name)
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
# -*- coding: utf-8 -*-
import sys, os, glob, re
from wolfrpg import commands, maps, databases, gamedats, common_events,route
from wolfrpg.service_fn import write_csv_list
from ruamel.yaml import YAML # NOTE: for debug and string search purposes

DUMP_YAML = True
yaml=YAML()
yaml.register_class(maps.Map)
yaml.register_class(maps.Map.Event)
yaml.register_class(maps.Map.Event.Page)
yaml.register_class(databases.Database)
yaml.register_class(databases.Database.Type)
yaml.register_class(databases.Database.Field)
yaml.register_class(databases.Database.Data)
yaml.register_class(common_events.CommonEvents)
yaml.register_class(common_events.CommonEvents.Event)
yaml.register_class(commands.Command)
yaml.register_class(commands.Blank)
yaml.register_class(commands.Checkpoint)
yaml.register_class(commands.Message)
yaml.register_class(commands.Choices)
yaml.register_class(commands.Comment)
yaml.register_class(commands.ForceStopMessage)
yaml.register_class(commands.DebugMessage)
yaml.register_class(commands.ClearDebugText)
yaml.register_class(commands.VariableCondition)
yaml.register_class(commands.StringCondition)
yaml.register_class(commands.SetVariable)
yaml.register_class(commands.SetString)
yaml.register_class(commands.InputKey)
yaml.register_class(commands.SetVariableEx)
yaml.register_class(commands.AutoInput)
yaml.register_class(commands.BanInput)
yaml.register_class(commands.Teleport)
yaml.register_class(commands.Sound)
yaml.register_class(commands.Picture)
yaml.register_class(commands.ChangeColor)
yaml.register_class(commands.SetTransition)
yaml.register_class(commands.PrepareTransition)
yaml.register_class(commands.ExecuteTransition)
yaml.register_class(commands.StartLoop)
yaml.register_class(commands.BreakLoop)
yaml.register_class(commands.BreakEvent)
yaml.register_class(commands.EraseEvent)
yaml.register_class(commands.ReturnToTitle)
yaml.register_class(commands.EndGame)
yaml.register_class(commands.StopNonPic)
yaml.register_class(commands.ResumeNonPic)
yaml.register_class(commands.LoopTimes)
yaml.register_class(commands.Wait)
yaml.register_class(commands.Move)
yaml.register_class(commands.WaitForMove)
yaml.register_class(commands.CommonEvent)
yaml.register_class(commands.CommonEventReserve)
yaml.register_class(commands.SetLabel)
yaml.register_class(commands.JumpLabel)
yaml.register_class(commands.SaveLoad)
yaml.register_class(commands.LoadGame)
yaml.register_class(commands.SaveGame)
yaml.register_class(commands.MoveDuringEventOn)
yaml.register_class(commands.MoveDuringEventOff)
yaml.register_class(commands.Chip)
yaml.register_class(commands.ChipSet)
yaml.register_class(commands.Database)
yaml.register_class(commands.ImportDatabase)
yaml.register_class(commands.Party)
yaml.register_class(commands.MapEffect)
yaml.register_class(commands.ScrollScreen)
yaml.register_class(commands.Effect)
yaml.register_class(commands.CommonEventByName)
yaml.register_class(commands.ChoiceCase)
yaml.register_class(commands.SpecialChoiceCase)
yaml.register_class(commands.ElseCase)
yaml.register_class(commands.CancelCase)
yaml.register_class(commands.LoopEnd)
yaml.register_class(commands.BranchEnd)
yaml.register_class(route.RouteCommand)

STRINGS_NAME = "strings"
ATTRIBUTES_NAME = "attributes"
STRINGS_DB_POSTFIX = "_" + STRINGS_NAME + ".csv"
ATTRIBUTES_DB_POSTFIX = "_" + ATTRIBUTES_NAME + ".csv"
REPLACEMENT_TAGS_RE = r'(?:「|」|(?:\\[A-Za-z\d]+\[\d+\]|\\[A-Za-z\d<>]+))'

def search_resource(path, name):
    files = glob.glob(os.path.join(path, "**", name), recursive = True)
    return files if len(files) else []

def is_translatable(text):
    return text and "\u25A0" != text

def attributes_of_command(command):
    if isinstance(command, commands.Choices):
        return [i.replace('\r\n', '\n') for i in command.text if is_translatable(i)]
    elif isinstance(command, commands.Database):
        return [command.text.replace('\r\n', '\n')] if is_translatable(command.text) else []
    elif isinstance(command, commands.StringCondition):
        return [i.replace('\r\n', '\n') for i in command.string_args if is_translatable(i)]
    elif isinstance(command, commands.SetString):
        return [command.text.replace('\r\n', '\n')] if is_translatable(command.text) else []
    elif isinstance(command, commands.Picture):
        if command.ptype == 'text':
            return [command.text.replace('\r\n', '\n')] if is_translatable(command.text) else []
    return []

def strings_of_command(command):
    if isinstance(command, commands.Message):
        return [command.text.replace('\r\n', '\n')] if is_translatable(command.text) else []
    return []

def get_context(command):
    return ''

def make_csv_field(text, context, translation=''):
    return [text, translation]#, get_context(command)]

def make_postfixed_name(name, postfix):
    return os.path.join(os.path.dirname(name), name + postfix)

def remove_ext(name):
    name = name.split('.')
    return '.'.join(name[:-1])

def write_translations(name, attrs, strs):
    name = remove_ext(name)
    write_csv_list(make_postfixed_name(name, ATTRIBUTES_DB_POSTFIX), attrs)
    write_csv_list(make_postfixed_name(name, STRINGS_DB_POSTFIX), strs)

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
    map_names = search_resource(os.getcwd(), '*.mps') # map data
    commonevents_name = search_resource(os.getcwd(), 'CommonEvent.dat') # common events
    dat_name = search_resource(os.getcwd(), 'Game.dat') # basic data
    db_names = list(filter(lambda x: "wolfrpg" not in x and "SysDataBaseBasic" not in x, search_resource(
        os.getcwd(), '*.project'))) # projects

    tags = []

    #maps_cache = dict()
    for map_name in map_names:
        print('Extracting',os.path.basename(map_name) +'...')
        translatable_attrs_set = set()
        translatable_strings = []
        mp = maps.Map(map_name)
        #maps_cache[map_name] = mp
        for event in mp.events:
            for page in event.pages:
                for i, command in enumerate(page.commands):
                    a = attributes_of_command(command)
                    if len(a):
                        translatable_attrs_set = translatable_attrs_set.union(a)
                    s = strings_of_command(command)
                    if len(s):
                        translatable_strings += [make_csv_field(strn, command) for strn in s]
        translatable_attrs = [make_csv_field(attr, command) for attr in translatable_attrs_set]
        write_translations(map_name, translatable_attrs, translatable_strings)
        tags += search_tags(translatable_attrs)
        tags += search_tags(translatable_strings)
        if DUMP_YAML:
            with open(remove_ext(map_name) + '.yaml', mode='w', encoding='utf-8') as f: yaml.dump(mp, f)

    if len(commonevents_name):
        commonevents_name = commonevents_name[0]
        ce = common_events.CommonEvents(commonevents_name)
        translatable_attrs_set = set()
        translatable_strings = []
        print('Extracting',os.path.basename(commonevents_name) +'...')
        for event in ce.events:
            for i, command in enumerate(event.commands):
                a = attributes_of_command(command)
                if len(a):
                    translatable_attrs_set = translatable_attrs_set.union(a)
                s = strings_of_command(command)
                if len(s):
                    translatable_strings += [make_csv_field(strn, command) for strn in s]
        translatable_attrs = [make_csv_field(attr, command) for attr in translatable_attrs_set]
        write_translations(commonevents_name, translatable_attrs, translatable_strings)
        tags += search_tags(translatable_attrs)
        tags += search_tags(translatable_strings)
        if DUMP_YAML:
            with open(remove_ext(commonevents_name) + '.yaml', mode='w', encoding='utf-8') as f: yaml.dump(ce, f)

    for db_name in db_names:
        print('Extracting',os.path.basename(db_name) +'...')
        db_name_only = remove_ext(os.path.basename(db_name))
        db = databases.Database(db_name, os.path.join(os.path.dirname(db_name),  db_name_only + ".dat"))
        translatable = []
        for t in  db.types:
            for i, d in enumerate(t.data):
                for l in d.each_translatable():
                    if len(l) and len(l[0]):
                        translatable.append([l[0].replace('\r\n', '\n'), ''])#, f"DATABASE@{t.data.index}"])
        write_csv_list(os.path.join(os.path.dirname(db_name), db_name_only + ATTRIBUTES_DB_POSTFIX), translatable)
        tags += search_tags(translatable)
        if DUMP_YAML:
            with open(remove_ext(db_name) + '.yaml', mode='w', encoding='utf-8') as f: yaml.dump(db, f)

    if len(dat_name):
        dat_name = dat_name[0]
        gd = gamedats.GameDat(dat_name)
        translatable = []
        print('Extracting',os.path.basename(dat_name) +'...')
        if gd.title:
            translatable.append([gd.title, '', 'TITLE'])
        if gd.version:
            translatable.append([gd.version, '', 'VERSION'])
        if gd.font:
            translatable.append([gd.font, '', 'FONT'])
        if gd.subfonts:
            translatable += [[font, '', 'SUBFONT'] for font in gd.subfonts if font]
        dat_name_only = remove_ext(os.path.basename(dat_name))
        write_csv_list(os.path.join(os.path.dirname(dat_name), dat_name_only + ATTRIBUTES_DB_POSTFIX), translatable)

        tags = [[t, "a0%d_tg," % i] for i, t in enumerate(set(tags))]
        tags = sorted(tags, reverse=True, key=lambda x: len(x[0]))
        write_csv_list(os.path.join(os.getcwd(), 'replacement_tags.csv'), tags)

if __name__ == "__main__":
    main()
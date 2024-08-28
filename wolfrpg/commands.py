# -*- coding: utf-8 -*-
from .route import RouteCommand

##########################
# Map of CIDs to classes #
##########################


CID_TO_CLASS = {
    0: 'Blank',
    99: 'Checkpoint',
    101: 'Message',
    102: 'Choices',
    103: 'Comment',
    105: 'ForceStopMessage',
    106: 'DebugMessage',
    107: 'ClearDebugText',
    111: 'VariableCondition',
    112: 'StringCondition',
    121: 'SetVariable',
    122: 'SetString',
    123: 'InputKey',
    124: 'SetVariableEx',
    125: 'AutoInput',
    126: 'BanInput',
    130: 'Teleport',
    140: 'Sound',
    150: 'Picture',
    151: 'ChangeColor',
    160: 'SetTransition',
    161: 'PrepareTransition',
    162: 'ExecuteTransition',
    170: 'StartLoop',
    171: 'BreakLoop',
    172: 'BreakEvent',
    173: 'EraseEvent',
    174: 'ReturnToTitle',
    175: 'EndGame',
    176: 'StartLoop2',
    177: 'StopNonPic',
    178: 'ResumeNonPic',
    179: 'LoopTimes',
    180: 'Wait',
    201: 'Move', # special case
    202: 'WaitForMove',
    210: 'CommonEvent',
    211: 'CommonEventReserve',
    212: 'SetLabel',
    213: 'JumpLabel',
    220: 'SaveLoad',
    221: 'LoadGame',
    222: 'SaveGame',
    230: 'MoveDuringEventOn',
    231: 'MoveDuringEventOff',
    240: 'Chip',
    241: 'ChipSet',
    250: 'Database',
    251: 'ImportDatabase',
    270: 'Party',
    280: 'MapEffect',
    281: 'ScrollScreen',
    290: 'Effect',
    300: 'CommonEventByName',
    401: 'ChoiceCase',
    402: 'SpecialChoiceCase',
    420: 'ElseCase',
    421: 'CancelCase',
    498: 'LoopEnd',
    499: 'BranchEnd',
    999: 'Default',
   -1: 'Invalid'
}


class Command:
    def __init__(self, cid, args, string_args, indent):
        self.cid = cid
        self.args = args
        self.string_args = string_args
        self.indent = indent

    def terminate_stream(self, coder):
        coder.write_terminator()

    @staticmethod
    def create(coder):
        # Read all data for this command from file
        args_len = coder.read_u1() - 1
        _cid = coder.read_u4()
        _args = [coder.read_u4() for i in range(args_len)]

        _indent = coder.read_u1()
        string_args_len = coder.read_u1()
        _string_args = [coder.read_string() for i in range(string_args_len)]

        # Read the move list if necessary
        terminator = coder.read_u1()
        if terminator == 1:
            return Move(_cid, _args, _string_args, _indent, coder)
        elif terminator != 0:
            raise Exception("command terminator is an unexpected value (#{terminator})")

        # Create command
        obj = Command
        try:
            obj = globals()[CID_TO_CLASS[_cid]] # or getattr(cids, self.type.name, Command)
        except:
            pass
        return obj(_cid, _args, _string_args, _indent)

    def write(self, coder):
        coder.write_u1(len(self.args) + 1)
        coder.write_u4(self.cid)

        for arg in self.args:
            coder.write_u4(arg)
        coder.write_u1(self.indent)
        coder.write_u1(len(self.string_args))

        for arg in self.string_args:
            coder.write_string(arg)

        self.terminate_stream(coder)


class Blank(Command):
    pass

class Checkpoint(Command):
    pass

class Message(Command):
    @property
    def text(self):
        return self.string_args[0]

    @text.setter
    def text(self, value):
        self.string_args[0] = value

class Choices(Command):
    @property
    def text(self):
        return self.string_args

class Comment(Command):
    @property
    def text(self):
        return self.string_args

class ForceStopMessage(Command):
    pass

class DebugMessage(Command):
    @property
    def text(self):
        return self.string_args[0]

class ClearDebugText(Command):
    pass

class VariableCondition(Command):
    pass

class StringCondition(Command):
    pass

class SetVariable(Command):
    pass

class SetString(Command):
    @property
    def text(self):
        if len(self.string_args) > 0:
            return self.string_args[0]
        else:
            return ''

    @text.setter
    def text(self, value):
        if len(self.string_args) > 0:
            self.string_args[0] = value

class InputKey(Command):
    pass

class SetVariableEx(Command):
    pass

class AutoInput(Command):
    pass

class BanInput(Command):
    pass

class Teleport(Command):
    pass

class Sound(Command):
    pass

class Picture(Command):
    def __init__(self, cid, args, string_args, indent):
        super().__init__(cid, args, string_args, indent)

    @property
    def ptype(self):
        int_type = (self.args[0] >> 4) & 0x07
        if int_type == 0:
            return 'file'
        elif int_type == 1:
            return 'file_string'
        elif int_type == 2:
            return 'text'
        elif int_type == 3:
            return 'window_file'
        elif int_type == 4:
            return 'window_string'
        else:
            return None

    def pnum(self):
        return self.args[1]

    @property
    def text(self):
        if self.ptype != 'text':
            return None
            #raise Exception(f"picture type #{self.ptype} has no text")
        return '' if not self.string_args or (len(self.string_args) == 0) else self.string_args[0]

    @text.setter
    def text(self, value):
        if self.ptype != 'text':
            raise Exception(f"picture type #{self.ptype} has no text")

        if not self.string_args or (len(self.string_args) == 0):
            self.string_args = list(value)
        else:
            self.string_args[0] = value

    @property
    def filename(self):
        if self.ptype != 'file' and self.ptype != 'window_file':
            raise Exception(f"picture type #{self.ptype} has no filename")
        return self.string_args[0]

    @filename.setter
    def filename(self,value):
        if self.type != 'file' and self.ptype != 'window_file':
            raise Exception(f"picture type #{self.ptype} has no filename")
        self.string_args[0] = value


class ChangeColor(Command):
    pass

class SetTransition(Command):
    pass

class PrepareTransition(Command):
    pass

class ExecuteTransition(Command):
    pass

class StartLoop(Command):
    pass

class BreakLoop(Command):
    pass

class BreakEvent(Command):
    pass

class EraseEvent(Command):
    pass

class ReturnToTitle(Command):
    pass

class EndGame(Command):
    pass

class LoopToStart(Command):
    pass

class StartLoop2(Command):
    pass

class StopNonPic(Command):
    pass

class ResumeNonPic(Command):
    pass

class LoopTimes(Command):
    pass

class Wait(Command):
    pass

class Move(Command):
    def __init__(self, cid, args, string_args, indent, coder):
        super().__init__(cid, args, string_args, indent)

        # Read unknown data
        self.unknown = [coder.read_u1() for i in range(5)]
        # Read known data
        self.flags = coder.read_u1()

        # Read route
        route_len = coder.read_u4()
        self.route = [RouteCommand.create(coder) for i in range(route_len)]

    def terminate_stream(self, coder):
        coder.write_u1(1)
        for b in self.unknown: # 5 bytes
            coder.write_u1(b)
        coder.write_u1(self.flags)
        coder.write_u4(len(self.route))
        for pt in self.route:
            pt.write(coder)

class WaitForMove(Command):
    pass

class CommonEvent(Command):
    @property
    def text(self):
        return self.string_args

class CommonEventReserve(Command):
    pass

class SetLabel(Command):
    pass

class JumpLabel(Command):
    pass

class SaveLoad(Command):
    pass

class LoadGame(Command):
    pass

class SaveGame(Command):
    pass

class MoveDuringEventOn(Command):
    pass

class MoveDuringEventOff(Command):
    pass

class Chip(Command):
    pass

class ChipSet(Command):
    pass

class ChipOverwrite(Command):
    pass

class Database(Command):
    @property
    def text(self):
        if len(self.string_args) > 2:
            return self.string_args[2]
        else:
            return ''

    @text.setter
    def text(self, value):
        if len(self.string_args) > 2:
            self.string_args[2] = value

class ImportDatabase(Command):
    pass

class Party(Command):
    pass

class MapEffect(Command):
    pass

class ScrollScreen(Command):
    pass

class Effect(Command):
    pass

class CommonEventByName(Command):
    @property
    def text(self):
        return self.string_args

class ChoiceCase(Command):
    pass

class SpecialChoiceCase(Command):
    pass

class ElseCase(Command):
    pass

class CancelCase(Command):
    pass

class LoopEnd(Command):
    pass

class BranchEnd(Command):
    pass

class Default(Command):
    pass

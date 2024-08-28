# -*- coding: utf-8 -*-
from .filecoder import FileCoder
from .commands import Command

class CommonEvents():
    COMMON_MAGIC2 = b'\x00W\x00\x00OL\x00FC\x00\x8f'
    COMMON_MAGIC3 = b'\x00W\x00\x00OLUFC\x00\x90'

    def __init__(self, filename):
        self.events = []
        self.wolfversion = 2
        with FileCoder.open(filename, 'r') as coder:
            try:
                coder.verify(self.COMMON_MAGIC2)
                self.COMMON_MAGIC = self.COMMON_MAGIC2
            except:
                coder.verify(self.COMMON_MAGIC3)
                self.COMMON_MAGIC = self.COMMON_MAGIC3
                self.wolfversion = 3
                coder.is_utf8 = True

            events_len = coder.read_u4()
            print('events:', events_len)
            self.events = [None] * events_len
            for i in range(events_len):
                #print(i,'of',events_len)
                event = self.Event(coder)
                assert(event.id < events_len)
                self.events[event.id] = event

            self.last_terminator = coder.read_u1()
            if self.last_terminator != 0x8F and self.last_terminator != 0x90:
                raise Exception(f"CommonEvents terminator not 0x8F|0x90 (got {hex(terminator)})")

    def write(self, filename):
        with FileCoder.open(filename, 'w') as coder:
            coder.write(self.COMMON_MAGIC)
            coder.write_u4(len(self.events))
            for event in self.events:
                event.write(coder)
            coder.write_u1(self.last_terminator)

    def grep(self, needle):
        pass

    class Event():
        EVENT_MAGIC = b'\x0A\x00\x00\x00'
        EVENT_MAGIC3 = b'\x0B\x00\x00\x00'

        def __init__(self, coder):
            indicator = coder.read_u1()
            if indicator != 0x8E: # 142
                raise Exception(f"CommonEvent header indicator not 0x8E (got {hex(indicator)})")

            self.id = coder.read_u4()
            self.unknown1 = coder.read_u4()
            self.blank1 = coder.read(7)
            self.name = coder.read_string()

            commands_len = coder.read_u4()
            self.commands = [Command.create(coder) for _ in range(commands_len)]

            self.unknown11 = coder.read_string()
            self.description = coder.read_string()
            indicator = coder.read_u1()
            if indicator != 0x8F:
                raise Exception(f"CommonEvent data indicator not 0x8F (got {hex(indicator)})")

            self.unknown31 = None
            try:
                coder.verify(self.EVENT_MAGIC)
                self.unknown3 = coder.read_string_array(10)
            except:
                coder.verify(self.EVENT_MAGIC3)
                self.unknown3 = coder.read_string_array(10)
                self.unknown31 = coder.read_u4()
                self.unknown32 = coder.read_u1()

            coder.verify(self.EVENT_MAGIC)
            self.unknown4 = coder.read_byte_array(10)

            coder.verify(self.EVENT_MAGIC)
            self.unknown5 = [coder.read_string_array() for _ in range(10)]

            coder.verify(self.EVENT_MAGIC)
            self.unknown6 = [coder.read_int_array() for _ in range(10)]

            self.unknown7 = coder.read(0x1D)
            self.unknown8 = [coder.read_string() for _ in range(100)]

            indicator = coder.read_u1()
            if indicator != 0x91: # 145
                raise Exception(f"expected 0x91, got {hex(indicator)}")

            self.unknown9 = coder.read_string()
            indicator = coder.read_u1()
            if indicator == 0x91: # 145
                return

            self._is_0x92 = False
            if indicator != 0x92: # 146
                raise Exception(f"expected 0x92, got {hex(indicator)}")
            else:
                self._is_0x92 = True

            self.unknown10 = coder.read_string()
            self.unknown12 = coder.read_u4()
            indicator = coder.read_u1()
            if indicator != 0x92: # 146
                raise Exception(f"expected 0x92, got {hex(indicator)}")


        def write(self, coder):
            coder.write_u1(0x8E)
            coder.write_u4(self.id)
            coder.write_u4(self.unknown1)
            coder.write(self.blank1)
            coder.write_string(self.name)
            coder.write_u4(len(self.commands))
            for cmd in self.commands:
                cmd.write(coder)

            coder.write_string(self.unknown11)
            coder.write_string(self.description)

            coder.write_u1(0x8F)
            if self.unknown31 is None:
                coder.write(self.EVENT_MAGIC)
            else:
                coder.write(self.EVENT_MAGIC3)
            for s in self.unknown3:
                coder.write_string(s)

            if self.unknown31 is not None:
                coder.write_u4(self.unknown31)
                coder.write_u1(self.unknown32)

            coder.write(self.EVENT_MAGIC)
            for i in self.unknown4:
                coder.write_u1(i)

            coder.write(self.EVENT_MAGIC)
            for sa in self.unknown5:
                coder.write_u4(len(sa))
                for s in sa:
                    coder.write_string(s)

            coder.write(self.EVENT_MAGIC)
            for ia in self.unknown6:
                coder.write_u4(len(ia))
                for i in ia:
                    coder.write_u4(i)

            coder.write(self.unknown7)
            for s in self.unknown8:
                coder.write_string(s)

            coder.write_u1(0x91)
            coder.write_string(self.unknown9)
            if self._is_0x92:
                coder.write_u1(0x92)
                coder.write_string(self.unknown10)
                coder.write_u4(self.unknown12)
                coder.write_u1(0x92)
            else:
                coder.write_u1(0x91)

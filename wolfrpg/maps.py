# -*- coding: utf-8 -*-
from .filecoder import FileCoder
from .common_events import CommonEvents
from .route import RouteCommand
from .commands import Command
from wolfrpg.wenums import EncodingType
from .debuging import *
import os#, io#, re

class Map():
    MAP_MAGIC = b'\0\0\0\0\0\0\0\0\0\0WOLFM\0'

    MAP_EVENT_MARKER = 0x6F
    MAP_TERMINATOR = 0x66

    def __init__(self, filename):
        self.filename = filename
        with FileCoder.open(filename, 'r') as coder:
            try:
                coder.verify(self.MAP_MAGIC)
            except:
                raise

            self.encoding_type = coder.read_u4()
            coder.is_utf8 = EncodingType(self.encoding_type) == EncodingType.UNICODE

            self.attributes = coder.read_u4() # 100
            self.version = coder.read_u1() # 100, 101, 102 etc
            self.unknown_str = coder.read_string() # NOTE: なし = None

            event_count = 0
            self.tileset_id = coder.read_u4()

            # Read basic data
            self.width = coder.read_u4()
            self.height = coder.read_u4()

            event_count = coder.read_u4()
            self.no_tiles = False
            if self.encoding_type:
                v = coder.read_u4()
                if v == 0xFFFFFFFF: # -1
                    self.no_tiles = True
                else:
                    coder.skip(-4)

            print(f'{self.width} x {self.height}; events: {event_count}' + (' (no tiles)' if self.no_tiles else ''))

            self.events = []
            if event_count == 0 or event_count > 0xFFFFF: # NOTE: 1048575 events is unrealistic
                return

            if not self.no_tiles:
                # Read tiles
                tiles_length = self.width * self.height * 3 * 4
                self.tiles = coder.read(tiles_length)

            if coder.eof:
                return #TileMap.mps case

            # Read events
            indicator = coder.read_u1()
            while indicator == self.MAP_EVENT_MARKER: # 111
                self.events.append(self.Event(coder))
                indicator = coder.read_u1()

            if indicator != self.MAP_TERMINATOR:
                raise Exception(f"unexpected map terminator: {hex(indicator)}")
            if not coder.eof:
                raise Exception(f"file is not fully parsed")

    def write(self, filename):
        with FileCoder.open(filename, 'w') as coder:
            coder.write(self.MAP_MAGIC)
            coder.write_u4(self.encoding_type)
            coder.write_u4(self.attributes)
            coder.write_u1(self.version)
            coder.write_string(self.unknown_str)

            coder.write_u4(self.tileset_id)

            coder.write_u4(self.width)
            coder.write_u4(self.height)
            coder.write_u4(len(self.events))

            if self.encoding_type:
                if self.no_tiles:
                    coder.write_u4(0xffffffff)

            if not self.no_tiles:
                coder.write(self.tiles)

            for event in self.events:
                if not event: continue
                coder.write_u1(self.MAP_EVENT_MARKER)
                event.write(coder)

            coder.write_terminator(self.MAP_TERMINATOR)

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['filename']
        return state

    #--------DEBUG method that searches for a string somewhere in the map ----------
    #
    def grep(self, needle):
        for event in self.events:
            for page in event.pages:
                for line, command in enumerate(page.commands):
                    for arg in command.string_args:
                        m = re.compile(arg).match(needle)
                        if m:
                            print( f"{self.filename}/{event.id}/{page.id+1}/{line+1}: {command.cid}\n\t{command.args}\n\t{command.string_args}\n")
                            break

    def grep_cid(self, cid):
        for event in self.events:
            for page in event.pages:
                for line, command in enumerate(page.commands):
                    if command.cid == cid:
                        print(f"{self.filename}/{event.id}/{page.id+1}/{line+1}: {command.cid}\n\t{command.args}\n\t{command.string_args}\n")
    #-------------------------------------------------------------------------------

    class Event():
        EVENT_MAGIC1 = bytes([0x39, 0x30, 0x00, 0x00])
        EVENT_MAGIC2 = bytes([0x00, 0x00, 0x00, 0x00])
        EVENT_MARKER = 0x79
        EVENT_TERMINATOR = 0x70

        def __init__(self, coder):
            coder.verify(self.EVENT_MAGIC1)
            self.id = coder.read_u4()
            self.name = coder.read_string()
            self.x = coder.read_u4()
            self.y = coder.read_u4()
            page_count = coder.read_u4()
            self.pages = [None] * page_count

            coder.verify(self.EVENT_MAGIC2)
            # Read pages
            page_id = 0
            indicator = coder.read_u1()
            while indicator == self.EVENT_MARKER: # 121
                page = self.Page(coder, page_id)
                self.pages[page_id] = page
                page_id += 1
                indicator = coder.read_u1()

            if len(self.pages) != page_count:
                raise Exception(
                    f"expected {page_count} pages, but read {len(self.pages)}"
                )
            if indicator != self.EVENT_TERMINATOR: # 112
                raise Exception(f"unexpected event terminator: {hex(indicator)}")

        def write(self, coder):
            coder.write(self.EVENT_MAGIC1)
            coder.write_u4(self.id)
            coder.write_string(self.name)
            coder.write_u4(self.x)
            coder.write_u4(self.y)
            coder.write_u4(len(self.pages))
            coder.write(self.EVENT_MAGIC2)

            # Write pages
            for page in self.pages:
                coder.write_u1(self.EVENT_MARKER)
                page.write(coder)

            coder.write_terminator(self.EVENT_TERMINATOR)


        class Page():
            PAGE_TERMINATOR = 0x7A

            def __init__(self, coder, pid):
                self.id = pid

                # TODO: ??? is it -1?
                self.unknown1 = coder.read_u4()

                # TODO: further abstract graphics options
                self.graphic_name = coder.read_string()
                self.graphic_direction = coder.read_u1()
                self.graphic_frame = coder.read_u1()
                self.graphic_opacity = coder.read_u1()
                self.graphic_render_mode = coder.read_u1()

                # TODO: parse conditions
                self.conditions = coder.read(1 + 4 + 4*4 + 4*4)
                # TODO: parse movement options
                self.movement = coder.read(4)

                # TODO: further abstract flags
                self.flags = coder.read_u1()

                # TODO: further abstract flags
                self.route_flags = coder.read_u1()

                # Parse move route
                route_count = coder.read_u4()
                self.route = [RouteCommand.create(coder) for _ in range(route_count)]

                # Parse commands
                command_count = coder.read_u4()
                self.commands = [Command.create(coder) for _ in range(command_count)]

                self.features = coder.read_u4()
                self.shadow_graphic_num = coder.read_u1()
                self.collision_width = coder.read_u1()
                self.collision_height = coder.read_u1()

                if self.features > 3:
                    self.page_transfer = coder.read_u1()

                p_terminator = coder.read_u1()
                if p_terminator != self.PAGE_TERMINATOR:
                    raise Exception(f"unexpected page terminator: {hex(p_terminator)}")

            def write(self, coder):
                coder.write_u4(self.unknown1)

                coder.write_string(self.graphic_name)
                coder.write_u1(self.graphic_direction)
                coder.write_u1(self.graphic_frame)
                coder.write_u1(self.graphic_opacity)
                coder.write_u1(self.graphic_render_mode)

                coder.write(self.conditions)
                coder.write(self.movement)
                coder.write_u1(self.flags)
                coder.write_u1(self.route_flags)

                coder.write_u4(len(self.route))
                for pt in self.route:
                    pt.write(coder)

                coder.write_u4(len(self.commands))
                for cmd in self.commands:
                    cmd.write(coder)

                coder.write_u4(self.features)
                coder.write_u1(self.shadow_graphic_num)
                coder.write_u1(self.collision_width)
                coder.write_u1(self.collision_height)
                if self.features > 3:
                    coder.write_u1(self.page_transfer)

                coder.write_terminator(self.PAGE_TERMINATOR)

# -*- coding: utf-8 -*-
from .filecoder import FileCoder
from .common_events import CommonEvents
from .route import RouteCommand
from .commands import Command
from .debuging import *
import os#, re

class Map():
    #attr_reader :tileset_id
    #attr_reader :width
    #attr_reader :height
    #attr_reader :events

    #DEBUG
    #attr_reader :filename

    MAP_MAGIC_JP2 = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00WOLFM\x00\x00\x00\x00\x00d\x00\x00\x00e\x05\x00\x00\x00\x82\xc8\x82\xb5\x00'
    MAP_MAGIC_JP3 = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00WOLFM\x00U\x00\x00\x00d\x00\x00\x00f\x07\x00\x00\x00\xe3\x81\xaa\xe3\x81'
    MAP_MAGIC_JP31 = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00WOLFM\x00U\x00\x00\x00d\x00\x00\x00f\x01\x00\x00\x00\x00\x01\x00\x00\x00'
    MAP_MAGIC_EN2 = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00WOLFM\x00\x00\x00\x00\x00\x64\x00\x00\x00\x65\x03,\x00\x00\x00\x4e\x6f\x00'

    def __init__(self, filename):
        self.filename = filename
        self.wolfversion = 2

        with FileCoder.open(filename, 'r') as coder:
            try:
                coder.verify(self.MAP_MAGIC_JP2)
                self.MAP_MAGIC = self.MAP_MAGIC_JP2
                coder.is_utf8 = False
            except Exception as e:
                try:
                    coder.verify(self.MAP_MAGIC_JP3)
                    self.MAP_MAGIC = self.MAP_MAGIC_JP3
                    self.wolfversion = 3
                    coder.is_utf8 = True
                except:
                    coder.verify(self.MAP_MAGIC_JP31)
                    self.MAP_MAGIC = self.MAP_MAGIC_JP31

            self.tileset_id = coder.read_u4()
            if self.wolfversion == 3:
                self.unk1 = coder.read_u2()

            # Read basic data
            self.width = coder.read_u4()
            self.height = coder.read_u4()
            event_count = 0
            if (self.MAP_MAGIC != self.MAP_MAGIC_JP31):
                event_count = coder.read_u4()
            print(f'{self.width} x {self.height}; events: {event_count}')

            # Read tiles
            # TODO: interpret this data
            tiles_length = self.width * self.height * 3 * 4
            self.tiles = coder.read(tiles_length)
            
            self.events = []
            if coder.eof:
                return #TileMap.mps case

            # Read events
            indicator = coder.read_u1()
            while indicator == 0x6F:
                self.events.append(self.Event(coder))
                indicator = coder.read_u1()

            if indicator != 0x66:
                raise Exception(f"unexpected event indicator found: #{hex(indicator)}")
            if not coder.eof:
                raise Exception(f"file is not fully parsed")

    def write(self, filename):
        with FileCoder.open(filename, 'w') as coder:
            coder.write(self.MAP_MAGIC)
            coder.write_u4(self.tileset_id)
            if self.wolfversion == 3:
                coder.write_u2(self.unk1)
                coder.is_utf8 = True
            coder.write_u4(self.width)
            coder.write_u4(self.height)
            coder.write_u4(len(self.events))
            coder.write(self.tiles)
            for event in self.events:
                if not event: continue
                coder.write_u1(0x6F)
                event.write(coder)

            coder.write_u1(0x66)

    #---------------- DEBUG method that searches for a string somewhere in the map ----------------------
    #
    def grep(self, needle):
        for event in self.events:
            for page in event.pages:
                for line, command in enumerate(page.commands):
                    for arg in command.string_args:
                        m = re.compile(arg).match(needle)
                        if m:
                            print( f"#{self.filename}/#{event.id}/#{page.id+1}/#{line+1}: #{command.cid}\n\t#{command.args}\n\t#{command.string_args}\n")
                            break

    def grep_cid(self, cid):
        for event in self.events:
            for page in event.pages:
                for line, command in enumerate(page.commands):
                    if command.cid == cid:
                        print(f"#{self.filename}/#{event.id}/#{page.id+1}/#{line+1}: #{command.cid}\n\t#{command.args}\n\t#{command.string_args}\n")
    #----------------------------------------------------------------------------------------------------

    class Event():
        #attr_accessor :id
        #attr_accessor :name
        #attr_accessor :x
        #attr_accessor :y
        #attr_accessor :pages

        EVENT_MAGIC1 = bytes([0x39, 0x30, 0x00, 0x00])
        EVENT_MAGIC2 = bytes([0x00, 0x00, 0x00, 0x00])

        def __init__(self, coder):
            coder.verify(self.EVENT_MAGIC1)
            self.id = coder.read_u4()
            self.name = coder.read_string()
            self.x = coder.read_u4()
            self.y = coder.read_u4()
            pages_len = coder.read_u4()
            self.pages = [None] * pages_len

            coder.verify(self.EVENT_MAGIC2)
            # Read pages
            page_id = 0
            indicator = coder.read_u1()
            while indicator == 0x79: # 121
                page = self.Page(coder, page_id)
                self.pages[page_id] = page
                page_id += 1
                indicator = coder.read_u1()

            if indicator != 0x70: # 112
                raise Exception(f"unexpected event page indicator: #{hex(indicator)}")

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
                coder.write_u1(0x79)
                page.write(coder)

            coder.write_u1(0x70)


        class Page():
            #attr_accessor :id
            #attr_accessor :unknown1
            #attr_accessor :graphic_name
            #attr_accessor :graphic_direction
            #attr_accessor :graphic_frame
            #attr_accessor :graphic_opacity
            #attr_accessor :graphic_render_mode
            #attr_accessor :conditions
            #attr_accessor :movement
            #attr_accessor :flags
            #attr_accessor :route_flags
            #attr_accessor :route
            #attr_accessor :commands
            #attr_accessor :shadow_graphic_num
            #attr_accessor :collision_width
            #attr_accessor :collision_height

            COMMANDS_TERMINATOR = bytes([ 0x03, 0x00, 0x00, 0x00])

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
                routes_len = coder.read_u4()
                self.route = [RouteCommand.create(coder) for _ in range(routes_len)]

                # Parse commands
                commands_len = coder.read_u4()
                self.commands = [Command.create(coder) for _ in range(commands_len)]

                coder.verify(self.COMMANDS_TERMINATOR)

                # TODO: abstract these options
                self.shadow_graphic_num = coder.read_u1()
                self.collision_width = coder.read_u1()
                self.collision_height = coder.read_u1()

                terminator = coder.read_u1()
                if terminator != 0x7A:
                    raise Exception(f"page terminator not 7A (found #{hex(terminator)})")


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
                for rt in self.route:
                    rt.write(coder)

                coder.write_u4(len(self.commands))
                for cmd in self.commands:
                    cmd.write(coder)
                coder.write(self.COMMANDS_TERMINATOR)

                coder.write_u1(self.shadow_graphic_num)
                coder.write_u1(self.collision_width)
                coder.write_u1(self.collision_height)
                coder.write_u1(0x7A)



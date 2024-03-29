﻿from io import StringIO
from .filecoder import FileCoder

class GameDat():
    #attr_accessor 'unknown1'
    #attr_accessor 'file_version' # only a guess
    #attr_accessor 'title'
    #attr_accessor 'unknown2'
    #attr_accessor 'font'
    #attr_accessor 'subfonts'
    #attr_accessor 'default_pc_graphic'
    #attr_accessor 'version'
    #attr_accessor 'unknown3'

    SEED_INDICES = [0, 8, 6]
    #XSEED_INDICES = [3, 4, 5]

    MAGIC_NUMBER2 = b'W\x00\x00OL\x00FM\x00'
    MAGIC_NUMBER3 = b'W\x00\x00OL\x00FMU'
    MAGIC_STRING = "0000-0000"

    @property
    def encrypted(self):
        return self.crypt_header != None

    def __init__(self, filename):

        with FileCoder.open(filename, 'r', self.SEED_INDICES) as coder:
            if coder.encrypted:
                self.crypt_header = coder.crypt_header
            else:
                self.crypt_header = None
                try:
                    coder.verify(self.MAGIC_NUMBER2)
                    self.MAGIC_NUMBER = self.MAGIC_NUMBER2
                except:
                    coder.verify(self.MAGIC_NUMBER3)
                    self.MAGIC_NUMBER = self.MAGIC_NUMBER3

            #TODO what is most of the junk in this file?
            self.unknown1 = coder.read_byte_array()
            self.file_version = coder.read_u4()
            self.title = coder.read_string()
            magic_string = coder.read_string()
            if magic_string != self.MAGIC_STRING:
                raise Exception(f"magic string is invalid (got #{magic_string})")

            self.unknown2 = coder.read_byte_array()

            self.font = coder.read_string()
            self.subfonts = [coder.read_string() for _ in range(3)]

            self.default_pc_graphic = coder.read_string()
            if self.file_version >= 9:
                self.version = coder.read_string()
            else:
                self.version = 0

            # This is the size of the file minus one. We don't need it, so discard.
            coder.skip(4)

            # NOTE: We don't care about the rest of this file for translation purposes.
            self.unknown3 = coder.read()


    def write(self, filename):
        with FileCoder.open(filename, 'w', self.SEED_INDICES, self.crypt_header) as coder:
            if not self.encrypted:
                coder.write(self.MAGIC_NUMBER)
            #if self.MAGIC_NUMBER == self.MAGIC_NUMBER3:
            #    coder.is_utf8 = True
            #else:
            #    coder.is_utf8 = False

            coder.write_byte_array(self.unknown1)
            coder.write_u4(self.file_version)
            coder.write_string(self.title)
            coder.write_string(self.MAGIC_STRING)
            coder.write_byte_array(self.unknown2)
            coder.write_string(self.font)
            for subfont in self.subfonts:
                coder.write_string(subfont)

            coder.write_string(self.default_pc_graphic)
            if self.file_version >= 9:
                coder.write_string(self.version)
            coder.write_u4(coder.tell + 4 + len(self.unknown3) - 1)
            coder.write(self.unknown3)


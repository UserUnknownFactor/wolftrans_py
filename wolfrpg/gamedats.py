from .filecoder import FileCoder
from io import BytesIO

class GameDat():
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
                    coder.is_utf8 = True

            self.unknown1 = coder.read_byte_array()
            self.string_count = coder.read_u4()

            self.title = coder.read_string() # string 0
            magic_string = coder.read_string()  # string 1
            if magic_string != self.MAGIC_STRING:
                raise Exception(f"magic string is invalid (got #{magic_string})")

            self.decrypt_key = coder.read_byte_array() # string 2

            self.font = coder.read_string() # string 3
            self.subfonts = [coder.read_string() for _ in range(3)] # strings 4, 5, 6

            self.default_pc_graphic = coder.read_string() # string 7

            if self.string_count >= 9:
                self.version  = coder.read_string() # string 8

            if self.string_count > 9:
                self.road_img      = coder.read_string() # string 9
                self.gauge_img  = coder.read_string() # string 10
                self.startup_msg  = coder.read_string() # string 11
                self.title_msg  = coder.read_string() # string 12

            self.file_size = coder.read_u4()
            real_size = coder.filesize()
            assert self.file_size == real_size, (
                f"size is unexpected; claims {self.file_size}, got: {real_size}")

            self.data = coder.read()

    def write(self, filename):
        stream = BytesIO()
        with FileCoder(stream, 'w', filename, self.SEED_INDICES, self.crypt_header) as coder:
            if not self.encrypted:
                coder.write(self.MAGIC_NUMBER)

            coder.write_byte_array(self.unknown1)
            coder.write_u4(self.string_count)
            coder.write_string(self.title)
            coder.write_string(self.MAGIC_STRING)
            coder.write_byte_array(self.decrypt_key)  # decrypt_key
            coder.write_string(self.font)

            for subfont in self.subfonts:
                coder.write_string(subfont)

            coder.write_string(self.default_pc_graphic)

            if self.string_count >= 9:
                coder.write_string(self.version)  # title_plus

            if self.string_count > 9:
                coder.write_string(self.road_img)
                coder.write_string(self.gauge_img)
                coder.write_string(self.startup_msg)
                coder.write_string(self.title_msg)

            new_size  = self.byte_size(coder)
            delta = new_size - self.file_size
            assert delta == 0, "Maintain the same modded bytesize " + (
                f"(diff: {('+' + str(delta)) if delta > 0 else delta}B) or use the Editor")
            coder.write_u4(new_size)  # file_size
            coder.write(self.data)

        with open(filename, 'wb') as f:
            stream.seek(0)
            f.write(stream.getbuffer())

    def byte_size(self, coder):
        size = 0
        size += len(self.MAGIC_NUMBER)
        size += len(self.unknown1) + 4
        size += 4  # for string_count
        size += coder.calc_string_size(self.title) + 4
        size += coder.calc_string_size(self.MAGIC_STRING) + 4
        size += len(self.decrypt_key) + 4
        size += coder.calc_string_size(self.font) + 4

        for subfont in self.subfonts:
            size += coder.calc_string_size(subfont) + 4

        size += coder.calc_string_size(self.default_pc_graphic) + 4

        if self.string_count >= 9:
            size += coder.calc_string_size(self.version) + 4

        if self.string_count > 9:
            size += coder.calc_string_size(self.road_img) + 4
            size += coder.calc_string_size(self.gauge_img) + 4
            size += coder.calc_string_size(self.startup_msg) + 4
            size += coder.calc_string_size(self.title_msg) + 4

        size += 4  # for file_size
        size += len(self.data)

        return size
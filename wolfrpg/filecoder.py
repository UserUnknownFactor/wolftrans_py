import struct, sys
from io import BytesIO, SEEK_CUR

DEBUG = True
this = sys.modules[__name__]
this.USE_UTF8_STRINGS = None
this.s_proj_key = None

def initialize(use_utf8: bool = False):
    if this.USE_UTF8_STRINGS is None:
        this.USE_UTF8_STRINGS = use_utf8
        print(f"UTF-8 strings: {this.USE_UTF8_STRINGS}")
    else:
        raise RuntimeError(f"UTF-8 usage already set to {this.USE_UTF8_STRINGS}.")

packer_u1 = struct.Struct('B')
packer_u4le = struct.Struct('<I') # Little-Endian
packer_u4be = struct.Struct('>I') # Big-Endian
packer_u2le = struct.Struct('<H') # Little-Endian
packer_u2be = struct.Struct('>H') # Big-Endian
packer_str = struct.Struct('s')

class FileCoder(object):
    #############
    # Constants #
    CRYPT_HEADER_SIZE = 10
    DECRYPT_INTERVALS = [1, 2, 5]

    ##############
    # Attributes #
    def __init__(self, io, mode, filename=None, seed_indices=None, crypt_header=None, is_db=False, self_io=False):
        self.io = io
        self.self_opened_io = self_io
        self.mode = mode
        self.filename = filename
        self.io.seek(0)
        self.is_be = False
        self.seed_indices = seed_indices
        self.crypt_header = crypt_header
        self.is_db = is_db
        self.is_utf8 = this.USE_UTF8_STRINGS

        if mode == 'r':
            self._handle_read_mode()
        elif mode == 'w':
            self._handle_write_mode()


    def _handle_read_mode(self):
        is_project = self.filename.endswith('.project')
        is_map = self.filename.endswith('.mps')
        is_game_dat = self.filename.endswith('Game.dat')

        if is_project:
            if this.s_proj_key is not None:
                from .wcrypto import decrypt_proj
                data = decrypt_proj(self.read(), this.s_proj_key)
                self.io.close()
                self.io = BytesIO(data)
                self.self_opened_io = False
        else:
            if not self.seed_indices and not is_map:
                return
            initial_byte = self.byte_at(1)
            if initial_byte == 0x50:
                from .wcrypto import decrypt_dat_v2
                data = self.read()
                data = decrypt_dat_v2(data)
                self.crypt_header = data[:143]
                self.io.close()
                self.io = BytesIO(data)
                self.self_opened_io = False
                self.skip(143)
                this.s_proj_key = self.crypt_header[0x14]
            elif is_map:
                packed = self.byte_at(20)
                if packed != 0x65:
                    return
                header = b'\0\0\0\0\0\0\0\0\0\0WOLFM\0U\0\0\0d\0\0\0f'
                self.skip(25)
                dec_data_size = self.read_u4()
                enc_data_size = self.read_u4()

                from lz4.block import decompress
                dec_data = decompress(self.read(enc_data_size), uncompressed_size=dec_data_size)
                assert dec_data_size == len(dec_data), "lz4 unpacked wrong size"

                self.io.close()
                self.io = BytesIO(header + dec_data)
                self.self_opened_io = False
            else:
                indicator = self.read_u1()
                if self.is_db:
                    if self.byte_at(1) != 0x50 or self.byte_at(5) != 0x54 or self.byte_at(7) != 0x4B:
                        return
                elif indicator == 0:
                    return
                from .wcrypto import decrypt_dat_v1
                header = indicator.to_bytes(1) + self.read(self.CRYPT_HEADER_SIZE - 1)
                seeds = [header[i] for i in self.seed_indices]
                dec_data = decrypt_dat_v1(self.read(), seeds, self.DECRYPT_INTERVALS)
                self.io.close()
                self.io = BytesIO(header + dec_data)
                self.self_opened_io = False
                if is_game_dat:
                    return

                self.skip(5)
                key_size = self.read_u4()
                proj_key = self.read_u1()

                if this.s_proj_key is None:
                    this.s_proj_key = proj_key

                self.skip(key_size - 1)

    def _handle_write_mode(self):
        if self.seed_indices and self.crypt_header:
            self.write(bytes(self.crypt_header))
        else:
            if self.seed_indices:
                self.write_u1(0)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    def close(self):
        if self.self_opened_io:
            self.io.close()

    ##################
    #  Class/static  #
    @classmethod
    def open(cls, source, mode, seed_indices=None, crypt_header=None, is_db=False):
        filename = ''
        if isinstance(source, str):
            stream = open(source, mode + 'b')
            filename = source
        return cls(stream, mode, filename, seed_indices, crypt_header, is_db=is_db, self_io=True)

    @staticmethod
    def print_stack():
        if not DEBUG: return
        import traceback
        for line in traceback.format_stack()[:-1]:
            print(line.strip())

    ########
    # Read #
    def read(self, size = None):
        # sanity check
        if size and size > 1024 * 1024 * 1024:
            self.print_stack()
            raise Exception(f"data of size = {size} is too big to read")
        if size:
            data = self.io.read(size)
            if len(data) != size:
                print(f"couldn't read required data of size {size} at\n")
                self.print_stack()
            return data
        else:
            return self.io.read()

    def read_u1(self):
        return packer_u1.unpack(self.io.read(1))[0]

    def read_u2(self):
        packer = packer_u2be if self.is_be else packer_u2le
        return packer.unpack(self.io.read(2))[0]

    def read_u4(self):
        packer = packer_u4be if self.is_be else packer_u4le
        return packer.unpack(self.io.read(4))[0]

    def read_string(self):
        size = self.read_u4()
        if size == 0:
            return ''
        elif size > 20000:
            self.print_stack()
            raise Exception(f"string of size {hex(size & 0xFFFFFFFF)} is improbable")

        _bstr = b''
        if size > 1:
            _bstr = self.read(size - 1)
        _last = self.read_u1()
        if _last != 0:
            self.print_stack()
            raise Exception("read string is not zero-terminated")

        _str = None
        encoding = 'utf-8' if self.is_utf8 else 'cp932'
        try:
            _str = _bstr.decode(encoding)
        except:
            self.print_stack()
            print(f"bad string encoding ({encoding}): {_bstr} (try -u switch if all strings err)")
            return _bstr.decode(encoding, errors='ignore')
        return _str

    def read_byte_array(self, arr_len = None):
        if arr_len is None:
            arr_len = self.read_u4()
        return [self.read_u1() for _ in range(arr_len)]

    def read_word_array(self, arr_len = None):
        if arr_len is None:
            arr_len = self.read_u4()
        return [self.read_u2() for _ in range(arr_len)]

    def read_int_array(self, arr_len = None):
        if arr_len is None:
            arr_len = self.read_u4()
        return [self.read_u4() for _ in range(arr_len)]

    def read_string_array(self, arr_len = None):
        if arr_len is None:
            arr_len = self.read_u4()
        return [self.read_string() for _ in range(arr_len)]

    def verify(self, expected, final=False):
        have = self.read(len(expected))
        if have != expected:
            self.io.seek(-len(expected), SEEK_CUR)
            #self.print_stack()
            if DEBUG and final:
                from .debuging import underline_differences
                underline_differences(expected, have)
            raise Exception(f"Verification failed: expected {expected}, got {have}")
        return True

    def skip(self, size):
        self.io.seek(size, SEEK_CUR)

    def peek(self, n_bytes=1):
        pos = self.io.tell()
        data = self.read(n_bytes)
        self.io.seek(pos)
        return data

    def delimit(self, i):
        if i % 16 == 0:
            print("\n")

    def dump(self, size):
        for i in range(size):
            print(" %02x" % self.read_u1(), end='')
            self.delimit(i)
        print("\n")

    def dump_until(self, pattern):
        _str = b''
        while not _str.ends_with(pattern):
            _str = self.io.read(1)
        for i in range(0, len(_str) - len(pattern)):
            print(" %02x" % _str[i], end='')
            self.delimit(i)
        print("\n")

    def filesize(self):
        pos = self.io.tell()
        size = self.io.seek(-1, 2)
        self.io.seek(pos)
        return size

    def byte_at(self, pos):
        pos_old = self.io.tell()
        self.io.seek(pos)
        ret = self.read_u1()
        self.io.seek(pos_old)
        return ret

    #########
    # Write #
    def write(self, data):
        if data is None: return 0
        nb = len(data)
        if nb > 0 and self.io.write(data) != nb:
            raise Exception("not all of %d bytes written" %(nb,))
        return nb

    def write_terminator(self, _byte = 0):
        self.write_u1(_byte)

    def write_u1(self, data):
        self.io.write(packer_u1.pack(data))

    def write_u2(self, data):
        packer = packer_u2be if self.is_be else packer_u2le
        self.io.write(packer.pack(data))

    def write_u4(self, data):
        packer = packer_u4be if self.is_be else packer_u4le
        self.io.write(packer.pack(data))

    def write_string(self, data):
        _str = None
        try:
            if not self.is_utf8:
                _str = data.encode('cp932')
            else:
                _str = data.encode('utf-8')
        except:
            try:
                _str = data.encode('utf-8')
            except:
                pass
        if _str is None:
            raise Exception(f'Failed to save string {data}')
        self.write_u4(len(_str) + 1)
        self.write(_str)
        self.write_terminator()

    def write_byte_array(self, data, with_length=True):
        if with_length:
            self.write_u4(len(data))
        for b in data:
            self.write_u1(b)

    def write_word_array(self, data, with_length=True):
        if with_length:
            self.write_u4(len(data))
        for b in data:
            self.write_u2(b)

    def write_int_array(self, data, with_length=True):
        if with_length:
            self.write_u4(len(data))
        for i in data:
            self.write_u4(i)

    def write_string_array(self, data, with_length=True):
        if with_length:
            self.write_u4(len(data))
        for s in data:
            self.write_string(s)

    #########
    #   Other  #
    def calc_string_size(self, data):
        size = -1
        try:
            if not self.is_utf8:
                _str = data.encode('cp932')
                size = len(_str)
            else:
                _str = data.encode('utf-8')
                size = len(_str)
        except:
            _str = data.encode('utf-8')
            size = len(_str)
        return size + 1

    @property
    def encrypted(self):
        return bool(self.crypt_header)

    @property
    def eof(self):
        io = self.io
        if io.read(1) == b'':
            return True
        else:
            io.seek(-1, SEEK_CUR)
        return False

    @property
    def tell(self):
        pos = self.io.tell()
        return (pos + self.CRYPT_HEADER_SIZE) if self.encrypted else pos

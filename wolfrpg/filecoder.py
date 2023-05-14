import struct, sys
from io import StringIO, SEEK_CUR, SEEK_END

this = sys.modules[__name__]
this.USE_UTF8_STRINGS = None

def initialize(use_utf8: bool = False):
    if (this.USE_UTF8_STRINGS is None):
        this.USE_UTF8_STRINGS = use_utf8
        print("UTF-8 strings:", USE_UTF8_STRINGS)
    else:
        raise RuntimeError(f"UTF-8 usage already set to {USE_UTF8_STRINGS}.")

class FileCoder(object):
    #############
    # Constants #
    CRYPT_HEADER_SIZE = 10
    DECRYPT_INTERVALS = [1, 2, 5]

    packer_u1 = struct.Struct('B')
    packer_u4le = struct.Struct('<I') # Little-Endian
    packer_u4be = struct.Struct('>I') # Big-Endian
    packer_u2le = struct.Struct('<H') # Little-Endian
    packer_u2be = struct.Struct('>H') # Big-Endian
    packer_str = struct.Struct('s')

    ##############
    # Attributes #
    def __init__(self, io, crypt_header = None, filename = None, seed_indices = None):
        self.io = io
        self.crypt_header = crypt_header
        self.filename = filename
        self.io.seek(0)
        self.is_be = False
        if USE_UTF8_STRINGS is None:
            raise Exception("Please specify string encoding via filecoder.initialize() method")
        self.is_utf8 = USE_UTF8_STRINGS

    def __enter__(self):
        return self

    @property
    def encrypted(self):
        return self.crypt_header != None

    #################
    # Class methods #

    @staticmethod
    def get_indices(seed_indices, header):
        return [header[i] for i in range(0, len(header)) if i in seed_indices]

    @staticmethod
    def open(filename, mode, seed_indices = None, crypt_header = None):
        if mode == 'r':
            coder = FileCoder(open(filename, 'rb'))

            # If encryptable, we need to make an extra check to see if it needs decrypting
            if seed_indices:
                indicator = coder.read_u1()
                while indicator != 0:
                    header = [indicator]
                    for _ in range(FileCoder.CRYPT_HEADER_SIZE - 1):
                        header.append(coder.read_u1())
                    seeds = FileCoder.get_indices(seed_indices, header) # seed_indices.map {|i| header[i]}
                    data = FileCoder.crypt(coder.read(), seeds)
                    coder = FileCoder(StringIO(data, 'rb'), header)
                    indicator = coder.read_u1()

        elif mode == 'w':
            # If encryptable, open a StringIO and pass the encryption options to the FileCoder
            if seed_indices and crypt_header:
                coder = FileCoder(StringIO(b'', 'wb'), crypt_header, filename, seed_indices)
                coder.write(bytes(crypt_header))
            else:
                coder = FileCoder(open(filename, 'wb'))
                if seed_indices:
                    coder.write_u1(0)

        return coder

    @staticmethod
    def print_stack():
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
        data = self.read(1)
        return self.packer_u1.unpack(data)[0]

    def read_u4(self):
        data = self.read(4)
        if self.is_be:
            return self.packer_u4be.unpack(data)[0]
        else:
            return self.packer_u4le.unpack(data)[0]

    def read_u2(self):
        data = self.read(2)
        if self.is_be:
            return self.packer_u2be.unpack(data)[0]
        else:
            return self.packer_u2le.unpack(data)[0]

    def read_string(self, encoding='utf-8'):
        size = self.read_u4()
        if size <= 0:
            self.print_stack()
            raise Exception(f"got a string of size {size} <= 0")
        if size > 30000:
            self.print_stack()
            raise Exception(f"the string of size {size} is improbable")
        _bstr = b''
        if size > 1:
            _bstr = self.read(size - 1)
        _last = self.read_u1()
        if _last != 0:
            self.print_stack()
            raise Exception("read string is not null-terminated")

        _str = None
        try:
            _str = _bstr.decode(encoding)
        except:
            try:
                if not self.is_utf8:
                    _str = _bstr.decode('cp932')
                else:
                    _str = _bstr.decode('utf-8')
            except:
                self.print_stack()
                print(f"bad string encoding for {encoding}/cp932: {_bstr}" )
                return _bstr.decode('unicode-escape')
        return _str

    def read_byte_array(self, arr_len = None):
        if arr_len is None:
            arr_len = self.read_u4()
        return [self.read_u1() for _ in range(arr_len)]

    def read_int_array(self, arr_len = None):
        if arr_len is None:
            arr_len = self.read_u4()
        return [self.read_u4() for _ in range(arr_len)]

    def read_string_array(self, arr_len = None):
        if arr_len is None:
            arr_len = self.read_u4()
        return [self.read_string() for _ in range(arr_len)]

    def verify(self, expected):
        have = self.read(len(expected))
        if have != expected:
            self.io.seek(-len(expected), SEEK_CUR)
            #self.print_stack()
            raise Exception(f"could not verify magic data (expecting #{expected}, got #{have})")
        return True

    def skip(self, size):
        self.io.seek(size, SEEK_CUR)

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
        self.write(self.packer_u1.pack(data))

    def write_u2(self, data):
        if self.is_be:
            self.write(self.packer_u2be.pack(data))
        else:
            self.write(self.packer_u2le.pack(data))

    def write_u4(self, data):
        if self.is_be:
            self.write(self.packer_u4be.pack(data))
        else:
            self.write(self.packer_u4le.pack(data))

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

    def write_byte_array(self, _bytes):
        self.write_u4(len(_bytes))
        for i in _bytes:
            self.write_u1(i)

    def write_int_array(self, _ints):
        self.write_u4(len(_ints))
        for i in _ints:
            self.write_u4(i)

    def write_string_array(self, _strings):
        self.write_u4(len(_strings))
        for s in _strings:
            self.write_string(s)

    #########
    # Other #
    def __exit__(self, *args, **kwargs):
        self.io.close()

    def close(self):
        if self.crypt_header and self.filename and self.seed_indices:
            with open(self.filename, 'wb') as f:
                f.write(bytes(self.crypt_header))
                seeds = FileCoder.get_indices(self.seed_indices, self.crypt_header) # @seed_indices.map{|i| crypt_header[i]}
                f.write(FileCoder.crypt(self.io.buffer, seeds))

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

    @staticmethod
    def crypt(data_str, seeds):
        data = bytearray(data_str)
        for s, seed in enumerate(seeds):
            for i in range(0, len(data), self.DECRYPT_INTERVALS[s]):
                seed = (seed * 0x343FD + 0x269EC3) & 0xFFFFFFFF
                data[i] ^= (seed >> 28) & 7

        return bytes(data)


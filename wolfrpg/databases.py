# -*- coding: utf-8 -*-
from .filecoder import FileCoder

class Database():
    DAT_SEED_INDICES = [0, 3, 9]
    DATABASE_MAGIC2 = b'W\x00\x00OL\x00FM\x00\xc1'
    DATABASE_MAGIC_CDB = b'W\x00\x00OLUFM\x00\xc2'
    DATABASE_MAGIC_G = b'W\x00\x00OL\x00FMU'
    UTF8 = False

    def __init__(self, project_filename, dat_filename):
        with FileCoder.open(project_filename, 'r') as coder:
            types_len = coder.read_u4()
            self.types = [self.Type(coder) for _ in range(types_len)]

        with FileCoder.open(dat_filename, 'r', self.DAT_SEED_INDICES) as coder:
            if coder.encrypted:
                self.crypt_header = coder.crypt_header
                self.unknown_encrypted_1 = coder.read_u1()
            else:
                self.crypt_header = None
                try:
                    coder.verify(self.DATABASE_MAGIC2)
                    self.DATABASE_MAGIC = self.DATABASE_MAGIC2
                    UTF8 = False
                except:
                    try:
                        coder.verify(self.DATABASE_MAGIC_CDB)
                        self.DATABASE_MAGIC = self.DATABASE_MAGIC_CDB
                        UTF8 = True
                    except:
                        coder.verify(self.DATABASE_MAGIC_G)
                        self.DATABASE_MAGIC = self.DATABASE_MAGIC_G
                        UTF8 = True

            num_types = coder.read_u4()
            if num_types != len(self.types):
                raise Exception("database .project and .dat files have mismatched Type count" +
                                f"(#{len(self.types)} vs. #{num_types})")

            [t.read_dat(coder) for t in self.types]
            self.last_terminator = coder.read_u1()
            if self.last_terminator != 0xC1 and self.last_terminator != 0xC2: # 193
                print(f"warning: no C1|C2 terminator at the of '#{dat_filename}', got {hex(self.last_terminator)} instead")

    @property
    def encrypted(self):
        return self.crypt_header != None

    def write(self, project_filename, dat_filename):
        with FileCoder.open(project_filename, 'w') as coder:
            coder.write_u4(len(self.types))
            [t.write_project(coder) for t in self.types]

        with FileCoder.open(dat_filename, 'w', self.DAT_SEED_INDICES, self.crypt_header) as coder:
            if coder.encrypted:
                coder.write_u1(self.unknown_encrypted_1)
            else:
                coder.write(self.DATABASE_MAGIC)

            coder.write_u4(len(self.types))
            [t.write_dat(coder) for t in self.types]
            coder.write_u1(self.last_terminator)

    def grep(self, needle=''):
        for type_index, t in enumerate(self.types):
            if not hasattr(t, 'data'): continue
            for datum_index, datum in enumerate(t.data):
                for value, field in datum.each_translatable():
                    if needle not in value: continue
                    print(f"DB:[#{type_index}]#{t.name}/[#{datum_index}]#{datum.name}/[#{field.index}]#{field.name}")
                    print( "\t" + value)


    class Type():
        #attr_accessor :name
        #attr_accessor :fields
        #attr_accessor :data
        #attr_accessor :description
        #attr_accessor :unknown1

        D_TYPE_SEPARATOR = b'\xFE\xFF\xFF\xFF'

        # Initialize from project file IO
        def __init__(self, coder):
            self.name = coder.read_string()
            fields_len = coder.read_u4()
            self.fields = [Database.Field(coder) for _ in range(fields_len)]

            data_len = coder.read_u4()
            self.data = [Database.Data(coder) for _ in range(data_len)]

            self.description = coder.read_string()

            # TODO: Add misc data to fields. It's separated for some reason.
            # This appears to always be 0x64, but save it anyway
            self.field_type_list_size = coder.read_u4()
            index = 0
            while index < len(self.fields):
                self.fields[index].ftype = coder.read_u1()
                index += 1

            coder.skip(self.field_type_list_size - index)

            u1_alen = coder.read_u4()
            for i in range(u1_alen):
                self.fields[i].unknown1 = coder.read_string()

            str_args_alen =  coder.read_u4()
            for i in range(str_args_alen):
                strs_len = coder.read_u4()
                self.fields[i].string_args = [coder.read_string() for _ in range(strs_len)]

            args_alen = coder.read_u4()
            for i in range(args_alen):
                ints_len = coder.read_u4()
                self.fields[i].args = [coder.read_u4() for _ in range(ints_len)]

            dafaults_alen = coder.read_u4()
            for i in range(dafaults_alen):
                self.fields[i].default_value = coder.read_u4()


        def write_project(self, coder):
            coder.write_string(self.name)
            coder.write_u4(len(self.fields))
            for field in self.fields:
                field.write_project(coder)

            coder.write_u4(len(self.data))
            for datum in self.data:
                datum.write_project(coder)

            coder.write_string(self.description)

            # Dump misc field data
            coder.write_u4(self.field_type_list_size)
            index = 0
            while index < len(self.fields):
                coder.write_u1(self.fields[index].ftype)
                index += 1

            while index < self.field_type_list_size:
                coder.write_u1(0)
                index += 1

            coder.write_u4(len(self.fields))
            for field in self.fields:
                coder.write_string(field.unknown1)

            coder.write_u4(len(self.fields))
            for field in self.fields:
                coder.write_u4(len(field.string_args))
                for arg in field.string_args:
                    coder.write_string(arg)

            coder.write_u4(len(self.fields))
            for field in self.fields:
                coder.write_u4(len(field.args))
                for arg in field.args:
                    coder.write_u4(arg)

            coder.write_u4(len(self.fields))
            for field in self.fields:
                coder.write_u4(field.default_value)



        # Read the rest of the data from the dat file
        def read_dat(self, coder):
            coder.verify(self.D_TYPE_SEPARATOR)
            self.unknown1 = coder.read_u4()
            fields_size = coder.read_u4()
            if fields_size != len(self.fields):
                self.fields = self.fields[0:fields_size]
            for field in self.fields:
                field.read_dat(coder)

            data_size = coder.read_u4()
            if data_size != len(self.data):
                self.data = self.data[0:data_size]
            for datum in self.data:
                datum.read_dat(coder, self.fields)


        def write_dat(self, coder):
            coder.write(self.D_TYPE_SEPARATOR)
            coder.write_u4(self.unknown1)
            coder.write_u4(len(self.fields))
            for field in self.fields:
                field.write_dat(coder)

            coder.write_u4(len(self.data))
            for datum in self.data:
                datum.write_dat(coder)

    class Field():
        #attr_accessor :name
        #attr_accessor :ftype
        #attr_accessor :unknown1
        #attr_accessor :string_args
        #attr_accessor :args
        #attr_accessor :default_value
        #attr_accessor :indexinfo

        STRING_START = 0x07D0
        INT_START = 0x03E8

        def __init__(self, coder):
            self.name = coder.read_string()

        def write_project(self, coder):
            coder.write_string(self.name)

        def read_dat(self, coder):
            self.indexinfo = coder.read_u4()

        def write_dat(self, coder):
            coder.write_u4(self.indexinfo)

        @property
        def is_string(self):
            return self.indexinfo >= self.STRING_START

        @property
        def is_int(self):
            return not self.is_string

        @property
        def index(self):
            if self.is_string:
                return self.indexinfo - self.STRING_START
            else:
                return self.indexinfo - self.INT_START


    class Data():
        #attr_accessor :name
        #attr_accessor :int_values
        #attr_accessor :string_values

        def __init__(self, coder):
            self.name = coder.read_string()

        def write_project(self, coder):
            coder.write_string(self.name)

        def read_dat(self, coder, fields):
            self.fields = fields
            self.int_values = []
            self.string_values = []

            for i in filter(lambda x: x.is_int, fields):
                self.int_values.append(coder.read_u4())

            for i in filter(lambda x: x.is_string, fields):
                self.string_values.append(coder.read_string())

        def write_dat(self, coder):
            for i in self.int_values:
                coder.write_u4(i)

            for i in self.string_values:
                coder.write_string(i)

        def get_field(self, key):
            if isinstance(key, Database.Field):
                if key.is_string:
                    return self.string_values[key.index]
                else:
                    return self.int_values[key.index]
            elif isinstance(key, int):
                return self.__dict__[self.fields[key]]
            else:
                raise Exception(f"Data.get_field() takes a Field, got #{key.__class__}")

        def set_field(self, key, value):
            if not isinstance(value, str):
                raise Exception(f"Data.set_field() takes a str, got #{value.__class__}")
            if isinstance(key, Database.Field):
                if key.is_string:
                    self.string_values[key.index] = value
                else:
                    self.int_values[key.index] = value
            elif isinstance(key, int):
                self.__dict__[self.fields[key]] = value
            else:
                raise Exception(f"Data.set_field() takes a Field, got #{key.__class__}")

        def each_translatable(self, all = False):
            for field in self.fields:
                if (not (field.is_string and field.ftype == 0)): continue
                #if field.name:
                #    yield (field.name, field)
                value = self.get_field(field)
                if value and value.replace('\r','').replace('\n','').strip():
                    if ".png" in value or ".mp3" in value or ".ogg" in value or ".wav" in value: continue
                    yield (value, field)



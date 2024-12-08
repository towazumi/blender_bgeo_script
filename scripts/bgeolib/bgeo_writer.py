# coding: utf-8

import struct
import io

class BinaryJsonWriter:

    class ArrayBlock:
        def __init__(self, writer):
            self.writer = writer

        def __enter__(self):
            self.writer.begin_array()
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.writer.end_array()

    class MapBlock:
        def __init__(self, writer):
            self.writer = writer

        def __enter__(self):
            self.writer.begin_map()
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.writer.end_map()


    def __init__(self):
        # UT_JID_MAGIC
        self.io = io.BytesIO()
        self.io.write(struct.pack('B', 0x7f))
        self.io.write(struct.pack('<L', 0x624a534e))

        self.string_map = dict()

    def __del__(self):
        self.io.close()

    def begin_array(self):
        self.io.write(b'[')

    def end_array(self):
        self.io.write(b']')

    def array_block(self):
        return BinaryJsonWriter.ArrayBlock(self)

    def begin_map(self):
        self.io.write(b'{')

    def end_map(self):
        self.io.write(b'}')

    def map_block(self):
        return BinaryJsonWriter.MapBlock(self)

    def write_length(self, length):
        if length<0:
            raise Exception('Try to write minus length.')

        if length<0xf1:
            self.io.write(struct.pack('B', length))

        # uint16_t
        elif length<=0xffff:
            self.io.write(struct.pack('<BH', 0xf2, length))

        # uint32_t
        elif length<=0xffffffff:
            self.io.write(struct.pack('<BL', 0xf4, length))

        # uint64_t
        else:
            self.io.write(struct.pack('<BQ', 0xf8, length))


    def write_idstring(self, string):

        if string not in self.string_map:
            value = len(self.string_map)
            self.string_map[string] = value

            bytes_array = string.encode('utf-8')

            #  id def
            self.io.write(b'+') # 0x2b
            self.write_length( value )
            self.write_length( len(bytes_array) )
            self.io.write(bytes_array)
            
        #  id ref
        value = self.string_map[string]
        self.io.write(b'&') # 0x26
        self.write_length( value )

    def write_string(self, string):
        
        bytes_array = string.encode('utf-8')

        self.io.write(b'\'') # 0x27
        self.write_length( len(bytes_array) )
        self.io.write(bytes_array)


    def write_bool(self, value):
        self.io.write(b'1' if value else b'0')

    def write_int(self, value):
        # int8_t 
        if -128<=value and value<=127:
            self.io.write(struct.pack('<Bb', 0x11, value))
        # int16_t 
        elif -32768<=value and value<=32767:
            self.io.write(struct.pack('<Bh', 0x12, value))
        # int32_t
        elif -2147483648<=value and value<=2147483647:
            self.io.write(struct.pack('<Bl', 0x13, value))
        # int64_t
        else:
            self.io.write(struct.pack('<Bq', 0x14, value))

    def write_int64(self, value):
        self.io.write(struct.pack('<Bq', 0x14, value))

    def write_real32(self, value):
        self.io.write(struct.pack('<Bf', 0x19, value))

    def write_real64(self, value):
        self.io.write(struct.pack('<Bd', 0x1a, value))

    def write_bool_uniform_array(self, values):
        self.io.write(struct.pack('<BB', 0x40, 0x10))
        self.write_length(len(values))

        bool_list = values[:]
        while len(bool_list)>0:
            current_list = bool_list[:32]
            word = 0
            for i, v in enumerate(current_list):
                if v:
                    word |= (1<<i)
            self.io.write(struct.pack('<L', word))

    def write_int8_uniform_array(self, values):
        self.io.write(struct.pack('<BB', 0x40, 0x11))
        length = len(values)
        self.write_length(length)
        if length>0:
            self.io.write(struct.pack('<{}b'.format(length), *values))

    def write_int16_uniform_array(self, values):
        self.io.write(struct.pack('<BB', 0x40, 0x12))
        length = len(values)
        self.write_length(length)
        if length>0:
            self.io.write(struct.pack('<{}h'.format(length), *values))

    def write_int32_uniform_array(self, values):
        self.io.write(struct.pack('<BB', 0x40, 0x13))
        length = len(values)
        self.write_length(length)
        if length>0:
            self.io.write(struct.pack('<{}l'.format(length), *values))

    def write_int64_uniform_array(self, values):
        self.io.write(struct.pack('<BB', 0x40, 0x14))
        length = len(values)
        self.write_length(length)
        if length>0:
            self.io.write(struct.pack('<{}q'.format(length), *values))

    def write_auto_int_uniform_array(self, values):

        if len(values)==0:
            self.write_int8_uniform_array( values )
            return

        min_value = max( values )
        max_value = max( values )

        # int8_t 
        if -128<=min_value and max_value<=127:
            self.write_int8_uniform_array( values )
        # int16_t 
        elif -32768<=min_value and max_value<=32767:
            self.write_int16_uniform_array( values )
        # int32_t
        elif -2147483648<=min_value and max_value<=2147483647:
            self.write_int32_uniform_array( values )
        # int64_t
        else:
            self.write_int64_uniform_array( values )


    def write_fpreal32_uniform_array(self, values):
        self.io.write(struct.pack('<BB', 0x40, 0x19))
        length = len(values)
        self.write_length(length)
        if length>0:
            self.io.write(struct.pack('<{}f'.format(length), *values))
        

    def write_fpreal64_uniform_array(self, values):
        self.io.write(struct.pack('<BB', 0x40, 0x1a))
        length = len(values)
        self.write_length(length)
        if length>0:
            self.io.write(struct.pack('<{}d'.format(length), *values))

    def write_uint8_uniform_array(self, values):
        self.io.write(struct.pack('<BB', 0x40, 0x21))
        length = len(values)
        self.write_length(length)
        if length>0:
            self.io.write(struct.pack('<{}B'.format(length), *values))
            
    def write_attribute_info(self, scope, typeinfo, name):
        self.write_idstring('scope')
        self.write_idstring(scope)

        self.write_idstring('type')
        self.write_idstring(typeinfo)

        self.write_idstring('name')
        self.write_idstring(name)

    def write_attribute_options(self, option):
        self.write_idstring('options')
        with self.map_block():
            if option is not None:
                self.write_idstring('type')
                with self.map_block():

                    self.write_idstring('type')
                    self.write_idstring('string')

                    self.write_idstring('value')
                    self.write_idstring(option)

    def write_attribute_size_storage(self, size, storage):
        self.write_idstring('size')
        self.write_int(size)

        self.write_idstring('storage')
        self.write_idstring(storage) 
    
    def fill(self, v, count):
        for i in range(0, count):
            self.io.write(v)

    def getvalue(self):
        return self.io.getvalue()


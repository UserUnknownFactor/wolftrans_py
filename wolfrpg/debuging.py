def dump_hex(bstr):
    for i in range(len(bstr)):
        print("%s " % hex(bstr[i]).replace('0x', ''), end='')
        if i > 0 and i % 16 == 0:
            print("")

# Find strings in binary string and return them inline in an array
def parse_strings(data):
    result = []

    # Scan for strings
    str_len = 0
    can_seek_multibyte = false
    for c, i in enumerate(bytes(data)):
        result = c

        if can_seek_multibyte:
            if (c >= 0x40 and c <= 0x9E and c != 0x7F) or (
                c >= 0xA0 and c <= 0xFC):
                str_len += 1
                continue

        if (c >= 0x81 and c <= 0x84) or (c >= 0x87 and c <= 0x9F) or (
            c >= 0xE0 and c <= 0xEA) or (c >= 0xED and c <= 0xEE) or (
                c >= 0xFA and c <= 0xFC):
            # head of multibyte character
            str_len += 1
            can_seek_multibyte = true
            continue


        can_seek_multibyte = false
        if c == 0x0A or c == 0x0D or c == 0x09 or ( # newline, CR, tab
                c >= 0x20 and c <= 0x7E) or ( # printable ascii
                c >= 0xA1 and c <= 0xDF): # half-width katakana
            str_len += 1
        else:
            _str = ''
            if c == 0 and str_len > 0:
                # Make sure it's valid by checking for a length prefix.
                str_len_check = struct.struct('V').unpack(data[i - str_len - 4, 4])[0]
                if str_len_check == str_len + 1:
                    _tmp = data[i - str_len, str_len]
                    try:
                        _str = _tmp.encode('utf-8')
                    except:
                        try:
                            _str = _tmp.encode('cp932')
                        except e:
                            raise e
                    finally:
                        pass
                        #do nothing

            # Either append the string or hex bytes
            if _str:
                result.slice(-(4 + str_len + 1), -1)
                result = _str

            # Reset _str length
            str_len = 0
    return result

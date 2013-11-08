# -*- coding: utf-8 -*-

from warnings import warn

# ---------------
#    ENCODING
# ---------------

def _encode_dictionary(input):
    result = str()
    for key, value in input.iteritems():
        result += bencode(key)+bencode(value)
    return 'd%se' % result

def _encode_integer(input):
    return 'i%de' % input

def _encode_iterable(input):
    result = str()
    for each in input:
        result += bencode(each)
    return 'l%se' % result

def _encode_string(input):
    if type(input) is unicode:
        input = input.encode('utf8')
    return '%d:%s' % (len(input),input)


# ---------------
#    DECODING
# ---------------

def _decode_dict(input):
    result = dict()
    remainder = input[1:]
    while remainder[0] != 'e':
        r = _decode_string(remainder)
        key = r[0]
        remainder = r[1]
        
        if remainder[0] == 'i':
            r = _decode_integer(remainder)
            value = r[0]
            result[key] = value
            remainder = r[1]
        
        elif remainder[0].isdigit():
            r = _decode_string(remainder)
            value = r[0]
            result[key] = value
            remainder = r[1]
        
        elif remainder[0] == 'l':
            r = _decode_list(remainder)
            value = r[0]
            result[key] = value
            remainder = r[1]
        
        elif remainder[0] == 'd':
            r = _decode_dict(remainder)
            value = r[0]
            result[key] = value
            remainder = r[1]
        
        else:
            raise ValueError("Invalid initial delimiter '%r' found while decoding a dictionary" % ramainder[0])
    
    return (result,remainder[1:])

def _decode_integer(input):
    end = input.find('e')
    if end>-1:
        return (int(input[1:end]),input[end+1:])
        end += 1
    else:
        raise ValueError("Missing ending delimiter 'e'")

def _decode_list(input):
    result = list()
    remainder = input[1:]
    while True:
        if remainder[0] == 'i':
            r = _decode_integer(remainder)
            result.append(r[0])
            remainder = r[1]
        
        elif remainder[0].isdigit():
            r = _decode_string(remainder)
            result.append(r[0])
            remainder = r[1]
        
        elif remainder[0] == 'l':
            r = _decode_list(remainder)
            result.append(r[0])
            remainder = r[1]
        
        elif remainder[0] == 'd':
            r = _decode_dict(remainder)
            result.append(r[0])
            remainder = r[1]
        
        elif remainder[0] == 'e':
            remainder = remainder[1:]
            break
        
        else:
            raise ValueError("Invalid initial delimiter '%r' found while decoding a list" % remainder[0])
    
    return (result,remainder)

def _decode_string(input):
    start = input.find(':')+1
    size = int(input[:start-1])
    end = start+size
    if end-start > len(input[start:]):
        print len(input[start:])
        warn("String is smaller than %d" % size, stacklevel=2)
    return (input[start:end], input[end:])



# -------------
#    PUBLIC
# -------------

def bencode(input):
    '''Encode python types to bencode format.
    
    Keyword arguments:
    input -- the input value to be encoded
    '''
    
    itype = type(input)
    
    if itype == type(str()) or itype == type(unicode()):
        return _encode_string(input.encode('utf8'))
    
    elif itype == type(float()):
        return _encode_string(str(input))
    
    elif itype == type(int()):
        return _encode_integer(input)
    
    elif itype == type(dict()):
        return _encode_dictionary(input)
    
    else:
        try:
            return _encode_iterable(iter(input))
        except TypeError:
            raise ValueError('Invalid field type: %r' % itype)


def bdecode(input):
    '''Decode strings from bencode format to python value types.
    
    Keyword arguments:
    input -- the input string to be decoded
    '''
    
    input = input.strip()
    
    if input[0] == 'i':
        return _decode_integer(input)[0]
    
    elif input[0].isdigit():
        return _decode_string(input)[0]
    
    elif input[0] == 'l':
        return _decode_list(input)[0]

    elif input[0] == 'd':
        return _decode_dict(input)[0]
    else:
        raise ValueError("Invalid initial delimiter '%s'" % input[0])

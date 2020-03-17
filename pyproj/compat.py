"""
This module is for compatibility between string types
"""


def cstrencode(pystr):
    """
    encode a string into bytes.  If already bytes, do nothing.
    """
    try:
        return pystr.encode("utf-8")
    except UnicodeDecodeError:
        return pystr.decode("utf-8").encode("utf-8")
    except AttributeError:
        return pystr  # already bytes


def pystrdecode(cstr):
    """
    Decode a string to a python string.
    """
    try:
        return cstr.decode("utf-8")
    except AttributeError:
        return cstr

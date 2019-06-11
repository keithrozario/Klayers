from collections import namedtuple


class ExtType(namedtuple('ExtType', 'code data')):
    """ExtType represents ext type in msgpack."""
    def __new__(cls, code, data):
        if not isinstance(code, int):
            raise TypeError("code must be int")
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        if not 0 <= code <= 127:
            raise ValueError("code must be 0~127")
        return super(ExtType, cls).__new__(cls, code, data)



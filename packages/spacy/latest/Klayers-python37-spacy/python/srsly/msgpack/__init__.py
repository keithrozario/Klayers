# coding: utf-8

import functools
from ._version import version
from .exceptions import *
from ._packer import Packer as _Packer
from ._unpacker import unpackb as _unpackb
from ._unpacker import unpack as _unpack
from ._unpacker import Unpacker as _Unpacker
from ._ext_type import ExtType
from ._msgpack_numpy import encode_numpy as _encode_numpy
from ._msgpack_numpy import decode_numpy as _decode_numpy


# msgpack_numpy extensions
class Packer(_Packer):
    def __init__(self, *args, **kwargs):
        kwargs['default'] = functools.partial(_encode_numpy, chain=kwargs.get('default'))
        super(Packer, self).__init__(*args, **kwargs)


class Unpacker(_Unpacker):
    def __init__(self, *args, **kwargs):
        kwargs['object_hook'] = functools.partial(_decode_numpy, chain=kwargs.get('object_hook'))
        super(Unpacker, self).__init__(*args, **kwargs)


def pack(o, stream, **kwargs):
    """
    Pack an object and write it to a stream.
    """
    packer = Packer(**kwargs)
    stream.write(packer.pack(o))


def packb(o, **kwargs):
    """
    Pack an object and return the packed bytes.
    """
    return Packer(**kwargs).pack(o)


def unpack(stream, **kwargs):
    """
    Unpack a packed object from a stream.
    """
    if 'object_pairs_hook' not in kwargs:
        object_hook = kwargs.get('object_hook')
        kwargs['object_hook'] = functools.partial(_decode_numpy, chain=object_hook)
    return _unpack(stream, **kwargs)


def unpackb(packed, **kwargs):
    """
    Unpack a packed object.
    """
    if 'object_pairs_hook' not in kwargs:
        object_hook = kwargs.get('object_hook')
        kwargs['object_hook'] = functools.partial(_decode_numpy, chain=object_hook)
    return _unpackb(packed, **kwargs)


# alias for compatibility to simplejson/marshal/pickle.
load = unpack
loads = unpackb

dump = pack
dumps = packb

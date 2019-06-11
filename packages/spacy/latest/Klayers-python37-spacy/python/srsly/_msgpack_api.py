# coding: utf8
from __future__ import unicode_literals

import gc

from . import msgpack
from .util import force_path


def msgpack_dumps(data):
    """Serialize an object to a msgpack byte string.

    data: The data to serialize.
    RETURNS (bytes): The serialized bytes.
    """
    return msgpack.dumps(data, use_bin_type=True)


def msgpack_loads(data, use_list=True):
    """Deserialize msgpack bytes to a Python object.

    data (bytes): The data to deserialize.
    use_list (bool): Don't use tuples instead of lists. Can make
        deserialization slower.
    RETURNS: The deserialized Python object.
    """
    # msgpack-python docs suggest disabling gc before unpacking large messages
    gc.disable()
    msg = msgpack.loads(data, raw=False, use_list=use_list)
    gc.enable()
    return msg


def write_msgpack(location, data):
    """Create a msgpack file and dump contents.

    location (unicode / Path): The file path.
    data: The data to serialize.
    """
    file_path = force_path(location, require_exists=False)
    with file_path.open("wb") as f:
        msgpack.dump(data, f, use_bin_type=True)


def read_msgpack(location, use_list=True):
    """Load a msgpack file.

    location (unicode / Path): The file path.
    use_list (bool): Don't use tuples instead of lists. Can make
        deserialization slower.
    RETURNS: The loaded and deserialized content.
    """
    file_path = force_path(location)
    with file_path.open("rb") as f:
        # msgpack-python docs suggest disabling gc before unpacking large messages
        gc.disable()
        msg = msgpack.load(f, raw=False, use_list=use_list)
        gc.enable()
        return msg

# coding: utf8
from __future__ import unicode_literals

from . import cloudpickle


def pickle_dumps(data, protocol=None):
    """Serialize a Python object with pickle.

    data: The object to serialize.
    protocol (int): Protocol to use. -1 for highest.
    RETURNS (bytest): The serialized object.
    """
    return cloudpickle.dumps(data, protocol=protocol)


def pickle_loads(data):
    """Deserialize bytes with pickle.

    data (bytes): The data to deserialize.
    RETURNS: The deserialized Python object.
    """
    return cloudpickle.loads(data)

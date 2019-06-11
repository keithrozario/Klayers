# coding: utf8
from __future__ import unicode_literals

from pathlib import Path


def force_path(location, require_exists=True):
    if not isinstance(location, Path):
        location = Path(location)
    if require_exists and not location.exists():
        raise ValueError("Can't read file: {}".format(location))
    return location

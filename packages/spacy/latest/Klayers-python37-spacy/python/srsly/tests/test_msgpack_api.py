# coding: utf8
from __future__ import unicode_literals

import pytest
import tempfile
from pathlib import Path
from contextlib import contextmanager
import shutil

from .._msgpack_api import read_msgpack, write_msgpack
from .._msgpack_api import msgpack_loads, msgpack_dumps


@contextmanager
def make_tempdir(files={}):
    temp_dir_str = tempfile.mkdtemp()
    temp_dir = Path(temp_dir_str)
    for name, content in files.items():
        path = temp_dir / name
        with path.open("wb") as file_:
            file_.write(content)
    yield temp_dir
    shutil.rmtree(temp_dir_str)


def test_msgpack_dumps():
    data = {"hello": "world", "test": 123}
    expected = [b"\x82\xa5hello\xa5world\xa4test{", b"\x82\xa4test{\xa5hello\xa5world"]
    msg = msgpack_dumps(data)
    assert msg in expected


def test_msgpack_loads():
    msg = b"\x82\xa5hello\xa5world\xa4test{"
    data = msgpack_loads(msg)
    assert len(data) == 2
    assert data["hello"] == "world"
    assert data["test"] == 123


def test_read_msgpack_file():
    file_contents = b"\x81\xa5hello\xa5world"
    with make_tempdir({"tmp.msg": file_contents}) as temp_dir:
        file_path = temp_dir / "tmp.msg"
        assert file_path.exists()
        data = read_msgpack(file_path)
    assert len(data) == 1
    assert data["hello"] == "world"


def test_read_msgpack_file_invalid():
    file_contents = b"\xa5hello\xa5world"
    with make_tempdir({"tmp.msg": file_contents}) as temp_dir:
        file_path = temp_dir / "tmp.msg"
        assert file_path.exists()
        with pytest.raises(ValueError):
            read_msgpack(file_path)


def test_write_msgpack_file():
    data = {"hello": "world", "test": 123}
    expected = [b"\x82\xa5hello\xa5world\xa4test{", b"\x82\xa4test{\xa5hello\xa5world"]
    with make_tempdir() as temp_dir:
        file_path = temp_dir / "tmp.msg"
        write_msgpack(file_path, data)
        with Path(file_path).open("rb") as f:
            assert f.read() in expected

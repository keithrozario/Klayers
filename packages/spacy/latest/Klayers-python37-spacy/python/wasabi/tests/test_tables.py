# coding: utf8
from __future__ import unicode_literals, print_function

import pytest
from wasabi.tables import table, row


@pytest.fixture()
def data():
    return [("Hello", "World", "12344342"), ("This is a test", "World", "1234")]


@pytest.fixture()
def header():
    return ["COL A", "COL B", "COL 3"]


@pytest.fixture()
def footer():
    return ["", "", "2030203.00"]


def test_table_default(data):
    result = table(data)
    assert (
        result
        == "\nHello            World   12344342\nThis is a test   World   1234    \n"
    )


def test_table_header(data, header):
    result = table(data, header=header)
    assert (
        result
        == "\nCOL A            COL B   COL 3   \nHello            World   12344342\nThis is a test   World   1234    \n"
    )


def test_table_header_footer_divider(data, header, footer):
    result = table(data, header=header, footer=footer, divider=True)
    assert (
        result
        == "\nCOL A            COL B   COL 3     \n--------------   -----   ----------\nHello            World   12344342  \nThis is a test   World   1234      \n--------------   -----   ----------\n                         2030203.00\n"
    )


def test_table_aligns(data):
    result = table(data, aligns=("r", "c", "l"))
    assert (
        result
        == "\n         Hello   World   12344342\nThis is a test   World   1234    \n"
    )


def test_table_aligns_single(data):
    result = table(data, aligns="r")
    assert (
        result
        == "\n         Hello   World   12344342\nThis is a test   World       1234\n"
    )


def test_table_widths():
    data = [("a", "bb", "ccc"), ("d", "ee", "fff")]
    widths = (5, 2, 10)
    result = table(data, widths=widths)
    assert result == "\na       bb   ccc       \nd       ee   fff       \n"


def test_row_single_widths():
    data = ("a", "bb", "ccc")
    result = row(data, widths=10)
    assert result == "a            bb           ccc       "

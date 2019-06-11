# coding: utf8
from __future__ import unicode_literals, print_function

import pytest
import traceback
from wasabi.traceback import TracebackPrinter


@pytest.fixture
def tb():
    return traceback.extract_stack()


def test_traceback_printer(tb):
    tbp = TracebackPrinter(tb_base="wasabi")
    msg = tbp("Hello world", "This is a test", tb=tb)
    print(msg)


def test_traceback_printer_highlight(tb):
    tbp = TracebackPrinter(tb_base="wasabi")
    msg = tbp("Hello world", "This is a test", tb=tb, highlight="kwargs")
    print(msg)


def test_traceback_printer_custom_colors(tb):
    tbp = TracebackPrinter(
        tb_base="wasabi", color_error="blue", color_highlight="green", color_tb="yellow"
    )
    msg = tbp("Hello world", "This is a test", tb=tb, highlight="kwargs")
    print(msg)


def test_traceback_printer_only_title(tb):
    tbp = TracebackPrinter(tb_base="wasabi")
    msg = tbp("Hello world", tb=tb)
    print(msg)


def test_traceback_printer_no_tb():
    tbp = TracebackPrinter(tb_base="wasabi")
    msg = tbp("Hello world", "This is a test")
    print(msg)

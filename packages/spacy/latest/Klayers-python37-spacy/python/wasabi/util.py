# coding: utf8
from __future__ import unicode_literals, print_function

import os
import sys
import textwrap


STDOUT_ENCODING = sys.stdout.encoding if hasattr(sys.stdout, "encoding") else None
ENCODING = STDOUT_ENCODING or "ascii"
NO_UTF8 = ENCODING.lower() not in ("utf8", "utf-8")


# Environment variables
ENV_ANSI_DISABLED = "ANSI_COLORS_DISABLED"  # no colors


class MESSAGES(object):
    GOOD = "good"
    FAIL = "fail"
    WARN = "warn"
    INFO = "info"


COLORS = {
    MESSAGES.GOOD: 2,
    MESSAGES.FAIL: 1,
    MESSAGES.WARN: 3,
    MESSAGES.INFO: 4,
    "red": 1,
    "green": 2,
    "yellow": 3,
    "blue": 4,
    "pink": 5,
    "cyan": 6,
    "white": 7,
    "grey": 8,
}


ICONS = {
    MESSAGES.GOOD: "\u2714" if not NO_UTF8 else "[+]",
    MESSAGES.FAIL: "\u2718" if not NO_UTF8 else "[x]",
    MESSAGES.WARN: "\u26a0" if not NO_UTF8 else "[!]",
    MESSAGES.INFO: "\u2139" if not NO_UTF8 else "[i]",
}


# Python 2 compatibility
IS_PYTHON_2 = sys.version_info[0] == 2

if IS_PYTHON_2:
    basestring_ = basestring  # noqa: F821
    input_ = raw_input  # noqa: F821
else:
    basestring_ = str
    input_ = input


def color(text, fg=None, bg=None, bold=False, underline=False):
    """Color text by applying ANSI escape sequence.

    text (unicode): The text to be formatted.
    fg (unicode / int): Foreground color. String name or 0 - 256 (see COLORS).
    bg (unicode / int): Background color. String name or 0 - 256 (see COLORS).
    bold (bool): Format text in bold.
    underline (bool): Underline text.
    RETURNS (unicode): The formatted text.
    """
    fg = COLORS.get(fg, fg)
    bg = COLORS.get(bg, bg)
    if not any([fg, bg, bold]):
        return text
    styles = []
    if bold:
        styles.append("1")
    if underline:
        styles.append("4")
    if fg:
        styles.append("38;5;{}".format(fg))
    if bg:
        styles.append("48;5;{}".format(bg))
    return "\x1b[{}m{}\x1b[0m".format(";".join(styles), text)


def wrap(text, wrap_max=80, indent=4):
    """Wrap text at given width using textwrap module.

    text (unicode): The text to wrap.
    wrap_max (int): Maximum line width, including indentation. Defaults to 80.
    indent (int): Number of spaces used for indentation. Defaults to 4.
    RETURNS (unicode): The wrapped text with line breaks.
    """
    indent = indent * " "
    wrap_width = wrap_max - len(indent)
    text = to_string(text)
    return textwrap.fill(
        text,
        width=wrap_width,
        initial_indent=indent,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    )


def format_repr(obj, max_len=50, ellipsis="..."):
    """Wrapper around `repr()` to print shortened and formatted string version.

    obj: The object to represent.
    max_len (int): Maximum string length. Longer strings will be cut in the
        middle so only the beginning and end is displayed, separated by ellipsis.
    ellipsis (unicode): Ellipsis character(s), e.g. "...".
    RETURNS (unicode): The formatted representation.
    """
    string = repr(obj)
    if len(string) >= max_len:
        half = int(max_len / 2)
        return "{} {} {}".format(string[:half], ellipsis, string[-half:])
    else:
        return string


def get_raw_input(description, default=False, indent=4):
    """Get user input from the command line via raw_input / input.

    description (unicode): Text to display before prompt.
    default (unicode or False/None): Default value to display with prompt.
    indent (int): Indentation in spaces.
    RETURNS (unicode): User input.
    """
    additional = " (default: {})".format(default) if default else ""
    prompt = wrap("{}{}: ".format(description, additional), indent=indent)
    user_input = input_(prompt)
    return user_input


def locale_escape(string, errors="replace"):
    """Mangle non-supported characters, for savages with ASCII terminals.

    string (unicode): The string to escape.
    errors (unicode): The str.encode errors setting. Defaults to `"replace"`.
    RETURNS (unicode): The escaped string.
    """
    string = to_string(string)
    string = string.encode(ENCODING, errors).decode("utf8")
    return string


def can_render(string):
    """Check if terminal can render unicode characters, e.g. special loading
    icons. Can be used to display fallbacks for ASCII terminals.

    string (unicode): The string to render.
    RETURNS (bool): Whether the terminal can render the text.
    """
    try:
        string.encode(ENCODING)
        return True
    except UnicodeEncodeError:
        return False


def supports_ansi():
    """Returns True if the running system's terminal supports ANSI escape
    sequences for color, formatting etc. and False otherwise. Inspired by
    Django's solution – hacky, but an okay approximation.

    RETURNS (bool): Whether the terminal supports ANSI colors.
    """
    if os.getenv(ENV_ANSI_DISABLED):
        return False
    # See: https://stackoverflow.com/q/7445658/6400719
    supported_platform = sys.platform != "Pocket PC" and (
        sys.platform != "win32" or "ANSICON" in os.environ
    )
    if not supported_platform:
        return False
    return True


def to_string(text):
    """Minimal compat helper to make sure text is unicode. Mostly used to
    convert Paths and other Python objects.

    text: The text/object to be converted.
    RETURNS (unicode): The converted string.
    """
    if not isinstance(text, basestring_):
        if IS_PYTHON_2:
            text = str(text).decode("utf8")
        else:
            text = str(text)
    return text

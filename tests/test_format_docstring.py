import os
import pytest
from simplecli.simplecli import format_docstring


def test_help_text_docstring_indent_simple():
    docstring = """
    stuff
      things
        more things
    """
    text = format_docstring(docstring)
    assert text == "stuff\n  things\n    more things".replace("\n", os.linesep)


def test_help_text_docstring_indent_hanging_whitespace():
    docstring = """
    stuff
      things
    """
    text = format_docstring(docstring)
    assert text == "stuff\n  things".replace("\n", os.linesep)


def test_help_text_docstring_empty():
    docstring = ""
    text = format_docstring(docstring)
    assert text == ""


def test_help_text_docstring_tab():
    docstring = "   \t foo"
    with pytest.raises(ValueError, match="tabs are not supported"):
        format_docstring(docstring)

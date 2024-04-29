# import pytest
from simplecli import simplecli
from typing import Optional


def test_int_no_default_no_comment():
    arg = simplecli.Param(
        name="count",
        line="   count: int",
        annotation=int,
    )
    assert arg.datatypes == [int]
    assert arg.default is simplecli.inspect._empty
    assert arg.optional is False
    assert arg.required is True
    assert arg.validate("test") is False
    assert arg.validate(True) is True
    assert arg.validate(False) is True
    assert arg.validate(100) is True
    assert arg.description == ""


def test_str_no_default_no_comment():
    arg = simplecli.Param(
        name="file_name",
        line="   file_name: str",
        annotation=str,
    )
    assert arg.datatypes == [str]
    assert arg.default is simplecli.inspect._empty
    assert arg.optional is False
    assert arg.required is True
    assert arg.validate("test") is True
    assert arg.validate(True) is True
    assert arg.validate(False) is True
    assert arg.validate(100) is True
    assert arg.description == ""


def test_str_no_default():
    arg = simplecli.Param(
        name="file_name",
        line="file_name: str  # Name of file",
        annotation=str,
    )
    assert arg.datatypes == [str]
    assert arg.default is simplecli.inspect._empty
    assert arg.optional is False
    assert arg.required is True
    assert arg.validate("test") is True
    assert arg.validate(True) is True
    assert arg.validate(False) is True
    assert arg.description == "Name of file"


def test_bool_no_comment_no_comma():
    arg = simplecli.Param(
        name="dry_run",
        line="   dry_run: bool = False",
        annotation=bool,
        default=False,
    )
    assert arg.datatypes == [bool]
    assert arg.default is False
    assert arg.optional is False
    assert arg.required is False
    assert arg.validate("test") is True
    assert arg.validate(True) is True
    assert arg.validate(100) is True
    assert arg.description == ""


def test_bool_no_comment():
    arg = simplecli.Param(
        name="dry_run",
        line="   dry_run: bool = False,",
        annotation=bool,
        default=False,
    )
    assert arg.datatypes == [bool]
    assert arg.default is False
    assert arg.optional is False
    assert arg.required is False
    assert arg.validate("test") is True
    assert arg.validate(True) is True
    assert arg.description == ""


def test_bool_comment():
    arg = simplecli.Param(
        name="dry_run",
        line="       dry_run: bool = False,  # Only show what would happen",
        annotation=bool,
        default=False,
    )
    assert arg.datatypes == [bool]
    assert arg.default is False
    assert arg.optional is False
    assert arg.required is False
    assert arg.validate("test") is True
    assert arg.validate(True) is True
    assert arg.description == "Only show what would happen"


def test_str_optional():
    arg = simplecli.Param(
        name="some_var",
        line="       some_var: Optional[str],",
        annotation=Optional[str],
    )
    assert arg.datatypes == [str, type(None)]
    assert arg.default is simplecli.inspect._empty
    assert arg.optional is True
    assert arg.required is False
    assert arg.validate("test") is True
    assert arg.validate(True) is True
    assert arg.description == ""

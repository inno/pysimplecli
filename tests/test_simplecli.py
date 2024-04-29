# import pytest
from simplecli import simplecli
from typing import Optional


def test_int_no_default_no_comment():
    arg = simplecli.Arg(
        name="count",
        line="   count: int",
        raw_datatype=int,
    )
    assert arg.datatypes == [int]
    assert arg.default is None
    assert arg.optional is False
    assert arg.required is True
    assert arg.validate("test") is False
    assert arg.validate(True) is True
    assert arg.validate(False) is True
    assert arg.validate(100) is True
    assert arg.description == ""


def test_str_no_default_no_comment():
    arg = simplecli.Arg(
        name="file_name",
        line="   file_name: str",
        raw_datatype=str,
    )
    assert arg.datatypes == [str]
    assert arg.default is None
    assert arg.optional is False
    assert arg.required is True
    assert arg.validate("test") is True
    assert arg.validate(True) is True
    assert arg.validate(False) is True
    assert arg.validate(100) is True
    assert arg.description == ""


def test_str_no_default():
    arg = simplecli.Arg(
        name="file_name",
        line="file_name: str  # Name of file",
        raw_datatype=str,
    )
    assert arg.datatypes == [str]
    assert arg.default is None
    assert arg.optional is False
    assert arg.required is True
    assert arg.validate("test") is True
    assert arg.validate(True) is True
    assert arg.validate(False) is True
    assert arg.description == "Name of file"


def test_bool_no_comment_no_comma():
    arg = simplecli.Arg(
        name="dry_run",
        line="   dry_run: bool = False",
        raw_datatype=bool,
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
    arg = simplecli.Arg(
        name="dry_run",
        line="   dry_run: bool = False,",
        raw_datatype=bool,
    )
    assert arg.datatypes == [bool]
    assert arg.default is False
    assert arg.optional is False
    assert arg.required is False
    assert arg.validate("test") is True
    assert arg.validate(True) is True
    assert arg.description == ""


def test_bool_comment():
    arg = simplecli.Arg(
        name="dry_run",
        line="       dry_run: bool = False,  # Only show what would happen",
        raw_datatype=bool,
    )
    assert arg.datatypes == [bool]
    assert arg.default is False
    assert arg.optional is False
    assert arg.required is False
    assert arg.validate("test") is True
    assert arg.validate(True) is True
    assert arg.description == "Only show what would happen"


def test_str_optional():
    arg = simplecli.Arg(
        name="some_var",
        line="       some_var: Optional[str],",
        raw_datatype=Optional[str],
    )
    assert arg.datatypes == [str, type(None)]
    assert arg.default is None
    assert arg.optional is True
    assert arg.required is False
    assert arg.validate("test") is True
    assert arg.validate(True) is True
    assert arg.description == ""

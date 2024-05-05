import pytest
import sys
from simplecli.simplecli import Param, help_text
from typing import Optional, Union


def min_py(major: int, minor: int) -> bool:
    return sys.version_info < (major, minor)


def test_help_text_union():
    text = help_text(
        filename="filename",
        params=[Param(name="somevar", annotation=Union[int, float])],
    )
    print(text)
    assert "[int, float]" in text
    assert "OPTIONAL" not in text


@pytest.mark.skipif(min_py(3, 10), reason="Union Type requires >= py3.10")
def test_help_text_uniontype():
    text = help_text(
        filename="filename",
        params=[Param(name="somevar", annotation=float | int)],
    )
    print(text)
    assert "[float, int]" in text
    assert "OPTIONAL" not in text


def test_help_text_optional():
    text = help_text(
        filename="filename",
        params=[Param(name="somevar", annotation=Optional[float])],
    )
    assert "float" in text
    assert "OPTIONAL" in text


def test_help_text_union_none():
    text = help_text(
        filename="filename",
        params=[Param(name="somevar", annotation=Union[float, None])],
    )
    assert "float" in text
    assert "OPTIONAL" in text


@pytest.mark.skipif(min_py(3, 10), reason="Union Type requires >= py3.10")
def test_help_text_uniontype_none():
    text = help_text(
        filename="filename",
        params=[Param(name="somevar", annotation=float | None)],
    )
    assert "float" in text
    assert "OPTIONAL" in text

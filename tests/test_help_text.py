from simplecli.simplecli import Param, help_text
from tests.utils import skip_if_uniontype_unsupported
from typing import Optional, Union


def test_help_text_union():
    text = help_text(
        filename="filename",
        params=[Param(name="somevar", annotation=Union[int, float])],
    )
    assert "[int, float]" in text
    assert "OPTIONAL" not in text


@skip_if_uniontype_unsupported
def test_help_text_uniontype():
    text = help_text(
        filename="filename",
        params=[Param(name="somevar", annotation=float | int)],
    )
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


@skip_if_uniontype_unsupported
def test_help_text_uniontype_none():
    text = help_text(
        filename="filename",
        params=[Param(name="somevar", annotation=float | None)],
    )
    assert "float" in text
    assert "OPTIONAL" in text

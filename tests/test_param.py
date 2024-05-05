import pytest
import re
from simplecli.simplecli import DefaultIfBool, Empty, Param
from typing import Union


def test_required_arguments():
    with pytest.raises(TypeError, match="name"):
        Param()
    p1 = Param(name="testparam")
    assert isinstance(p1, Param)
    p2 = Param("testparam")
    assert isinstance(p2, Param)
    assert p1 == p2


def test_equality():
    p1 = Param(name="testparam1", annotation=str)
    p2 = Param(name="testparam2", annotation=str)
    assert p1 != p2
    p3 = Param(name="testparam1", annotation=str)
    assert p1 == p3
    assert p1 != "a string"


def test_dunder_str():
    p1 = Param(name="testparam1", annotation=str)
    string1 = str(p1)
    assert re.search(r"testparam1", string1)
    assert re.search(r"value=Empty", string1)
    assert re.search(r"default=Empty", string1)
    assert re.search(r"required=True", string1)
    assert re.search(r"optional=False", string1)
    assert re.search(r"annotation=str", string1)

    p2 = Param(name="testparam2", annotation=str, default="testing")
    string2 = str(p2)
    assert re.search(r"testparam2", string2)
    assert re.search(r"value='testing'", string2)
    assert re.search(r"default='testing'", string2)
    assert re.search(r"required=False", string2)
    assert re.search(r"optional=False", string2)
    assert re.search(r"annotation=str", string2)


def test_help_name():
    p1 = Param(name="testparam1", annotation=str)
    p2 = Param(name="test_param_2", annotation=str)

    assert p1.help_name == "testparam1"
    assert p2.help_name == "test-param-2"


def test_help_type():
    p1 = Param(name="testparam1", annotation=str)
    assert p1.help_type == "str"

    p1 = Param(name="testparam1", annotation=Union[str, int])
    assert p1.help_type == "[str, int]"


def test_datatypes():
    p1 = Param(name="testparam1", annotation=str)
    assert p1.datatypes == [str]

    p2 = Param(name="testparam1", annotation=Union[str, float])
    assert p2.datatypes == [str, float]


def test_set_value():
    p1 = Param(name="testparam1", annotation=Union[int, float])
    with pytest.raises(ValueError, match="[int, float]"):
        p1.set_value("this is the value")

    with pytest.raises(ValueError, match="[int, float]"):
        p1.set_value(DefaultIfBool)
    assert p1.value is Empty
    p1.set_value(3)
    assert p1.value == 3

    p2 = Param(name="testparam2", annotation=bool)
    assert p2.value is Empty

    p2.set_value(DefaultIfBool)
    assert p2.value is True

    p2.set_value(False)
    assert p2.value is False

    p2 = Param(name="testparam2", annotation=bool, default=True)
    assert p2.value is True

    with pytest.raises(ValueError, match="list"):
        Param(name="testparam3", annotation=[str, bool])

    p3 = Param(name="testparam3", annotation=str)
    with pytest.raises(ValueError, match="requires a value"):
        p3.set_value(DefaultIfBool)


def test_union_uniontype():
    p1 = Param(name="testparam1", annotation=Union[str, float])
    assert p1.datatypes == [str, float]
    assert p1.help_type == "[str, float]"

    p2 = Param(name="testparam2", annotation=int | bool)
    assert p2.datatypes == [int, bool]
    assert p2.help_type == "[int, bool]"

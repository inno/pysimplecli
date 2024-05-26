import pytest
import sys
import typing
from simplecli import simplecli
from tests.utils import skip_if_uniontype_unsupported


@pytest.fixture(autouse=True)
def ensure_wrapped_not_flagged():
    simplecli._wrapped = False


def test_wrap_simple(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "123"])

    @simplecli.wrap
    def code(a: int):
        assert a == 123


def test_wrap_dupe(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "123"])

    def code1(a: int):
        pass

    def code2(a: int):
        pass

    code1_name = code1.__globals__["__name__"]
    code2_name = code2.__globals__["__name__"]
    with pytest.raises(SystemExit, match="only ONE"):
        code1.__globals__["__name__"] = "__main__"
        code2.__globals__["__name__"] = "__main__"
        simplecli.wrap(code1)
        simplecli.wrap(code2)
    code1.__globals__["__name__"] = code1_name
    code2.__globals__["__name__"] = code2_name


def test_wrap_help_simple(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--help"])

    def code1(this_var: int):  # stuff and things
        pass

    code1_name = code1.__globals__["__name__"]
    with pytest.raises(SystemExit) as e:
        code1.__globals__["__name__"] = "__main__"
        simplecli.wrap(code1)
    code1.__globals__["__name__"] = code1_name

    help_msg = e.value.args[0]
    assert "--this-var" in help_msg
    assert "stuff and things" in help_msg


def test_wrap_help_complex(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--help"])

    def code(
        that_var: typing.Union[str, int],  # that is the var
        not_this_var: typing.Optional[str],
        count: int = 54,  # number of things
    ):
        pass

    code_name = code.__globals__["__name__"]
    with pytest.raises(SystemExit) as e:
        code.__globals__["__name__"] = "__main__"
        simplecli.wrap(code)
    code.__globals__["__name__"] = code_name

    help_msg = e.value.args[0]
    assert "--that-var" in help_msg
    assert "that is the var" in help_msg
    assert "--count" in help_msg
    assert "Default: 54" in help_msg


def test_wrap_simple_type_error(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "123", "foo"])

    def code(a: int):
        pass

    code_name = code.__globals__["__name__"]
    with pytest.raises(SystemExit, match="Too many positional"):
        code.__globals__["__name__"] = "__main__"
        simplecli.wrap(code)
    code.__globals__["__name__"] = code_name


def test_wrap_simple_value_error(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "foo"])

    def code(a: int):
        pass

    code_name = code.__globals__["__name__"]
    with pytest.raises(SystemExit, match="must be of type int"):
        code.__globals__["__name__"] = "__main__"
        simplecli.wrap(code)
    code.__globals__["__name__"] = code_name


def test_wrap_version_absent(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--version"])

    def code2(this_var: int):  # stuff and things
        pass

    code2_name = code2.__globals__["__name__"]
    with pytest.raises(SystemExit) as e:
        code2.__globals__["__name__"] = "__main__"
        simplecli.wrap(code2)
    code2.__globals__["__name__"] = code2_name

    help_msg = e.value.args[0]
    assert "Description:" not in help_msg
    assert "version 1.2.3" not in help_msg
    assert "--this-var" in help_msg
    assert "stuff and things" in help_msg


def test_wrap_version_exists(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["super_script", "--version"])

    def code1(this_var: int):  # stuff and things
        pass

    code1_name = code1.__globals__["__name__"]
    with pytest.raises(SystemExit) as e:
        code1.__globals__["__name__"] = "__main__"
        code1.__globals__["__version__"] = "1.2.3"
        simplecli.wrap(code1)
    code1.__globals__["__name__"] = code1_name

    help_msg = e.value.args[0]
    assert "super_script version 1.2.3" in help_msg
    assert "Description:" not in help_msg
    assert "--this-var" not in help_msg
    assert "stuff and things" not in help_msg


def test_docstring(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--help"])

    def code2(this_var: int):  # stuff and things
        """
        this is a description
        """

    code2_name = code2.__globals__["__name__"]
    with pytest.raises(SystemExit) as e:
        code2.__globals__["__name__"] = "__main__"
        simplecli.wrap(code2)
    code2.__globals__["__name__"] = code2_name

    help_msg = e.value.args[0]
    assert "Description:" in help_msg
    assert "this is a description" in help_msg
    assert "--this-var" in help_msg
    assert "stuff and things" in help_msg


@skip_if_uniontype_unsupported
def test_wrap_uniontype(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--help"])

    def code(
        that_var: str | int,  # that is the var
        count: int = 54,  # number of things
    ):
        pass

    code_name = code.__globals__["__name__"]
    with pytest.raises(SystemExit) as e:
        code.__globals__["__name__"] = "__main__"
        simplecli.wrap(code)
    code.__globals__["__name__"] = code_name

    help_msg = e.value.args[0]
    assert "--that-var" in help_msg
    assert "that is the var" in help_msg
    assert "--count" in help_msg
    assert "Default: 54" in help_msg
    assert "OPTIONAL" not in help_msg


def test_wrap_simple_positional(capfd, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "1", "2", "3.5"])

    def code(a: int, b: int, c: typing.Union[int, float]):
        print(a + b + c)

    code_name = code.__globals__["__name__"]
    code.__globals__["__name__"] = "__main__"
    simplecli.wrap(code)
    (out, _) = capfd.readouterr()
    assert out.strip() == "6.5"
    code.__globals__["__name__"] = code_name


def test_wrap_boolean_false(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename"])

    @simplecli.wrap
    def code(is_false: bool = False):
        assert is_false is False


def test_wrap_boolean_false_invert(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--invert"])

    @simplecli.wrap
    def code(invert: bool = False):
        assert invert is True


def test_wrap_boolean_true(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename"])

    @simplecli.wrap
    def code(is_true: bool = True):
        assert is_true is True


def test_wrap_boolean_true_invert(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--invert"])

    @simplecli.wrap
    def code(invert: bool = True):
        assert invert is False


def test_wrap_boolean_true_no_default_invert(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--is-something"])

    @simplecli.wrap
    def code(is_something: bool):
        assert is_something is True


def test_wrap_boolean_true_no_default_no_arg(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename"])

    @simplecli.wrap
    def code(is_something: bool):
        assert is_something is False


def test_directly_called_wrap(monkeypatch):
    import tests.nested_test as nt

    assert nt.code(1, foo="test") == "2 test!"
    assert nt.code(test_id=2, foo="blarg") == "3 blarg!"


def test_wrap_no_typehint_(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "123"])

    def code1(foo):
        pass

    code1_name = code1.__globals__["__name__"]
    with pytest.raises(SystemExit, match="parameters need type hints!"):
        code1.__globals__["__name__"] = "__main__"
        simplecli.wrap(code1)
    code1.__globals__["__name__"] = code1_name


def test_wrap_no_typehint_no_arg(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename"])

    def code1(foo):
        pass

    code1_name = code1.__globals__["__name__"]
    with pytest.raises(SystemExit, match="ERROR: All wrapped function "):
        code1.__globals__["__name__"] = "__main__"
        simplecli.wrap(code1)
    code1.__globals__["__name__"] = code1_name


def test_wrap_no_typehint_kwarg(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--foo"])

    def code1(foo):
        pass

    code1_name = code1.__globals__["__name__"]
    with pytest.raises(SystemExit, match="function parameters need type"):
        code1.__globals__["__name__"] = "__main__"
        simplecli.wrap(code1)
    code1.__globals__["__name__"] = code1_name


def test_wrap_unsupported_type(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--foo"])

    def code1(foo: [str, int]):
        pass

    code1_name = code1.__globals__["__name__"]
    with pytest.raises(SystemExit, match="UnsupportedType: list"):
        code1.__globals__["__name__"] = "__main__"
        simplecli.wrap(code1)
    code1.__globals__["__name__"] = code1_name

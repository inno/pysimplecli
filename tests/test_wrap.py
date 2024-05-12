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

    with pytest.raises(SystemExit, match="only ONE"):
        code1.__globals__["__name__"] = "__main__"
        code2.__globals__["__name__"] = "__main__"
        simplecli.wrap(code1)
        simplecli.wrap(code2)


def test_wrap_help_simple(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--help"])

    def code1(this_var: int):  # stuff and things
        pass

    with pytest.raises(SystemExit) as e:
        code1.__globals__["__name__"] = "__main__"
        simplecli.wrap(code1)

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

    with pytest.raises(SystemExit) as e:
        code.__globals__["__name__"] = "__main__"
        simplecli.wrap(code)

    help_msg = e.value.args[0]
    assert "--that-var" in help_msg
    assert "that is the var" in help_msg
    assert "--count" in help_msg
    assert "Default: 54" in help_msg


def test_wrap_simple_type_error(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "123", "foo"])

    def code(a: int):
        pass

    with pytest.raises(SystemExit, match="Too many positional"):
        code.__globals__["__name__"] = "__main__"
        simplecli.wrap(code)


def test_wrap_simple_value_error(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "foo"])

    def code(a: int):
        pass

    with pytest.raises(SystemExit, match="must be of type int"):
        code.__globals__["__name__"] = "__main__"
        simplecli.wrap(code)


def test_wrap_version_absent(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--version"])

    def code2(this_var: int):  # stuff and things
        pass

    with pytest.raises(SystemExit) as e:
        code2.__globals__["__name__"] = "__main__"
        simplecli.wrap(code2)

    help_msg = e.value.args[0]
    assert "Description:" not in help_msg
    assert "Version: 1.2.3" not in help_msg
    assert "--this-var" in help_msg
    assert "stuff and things" in help_msg


def test_wrap_version_exists(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--version"])

    def code1(this_var: int):  # stuff and things
        pass

    with pytest.raises(SystemExit) as e:
        code1.__globals__["__name__"] = "__main__"
        code1.__globals__["__version__"] = "1.2.3"
        simplecli.wrap(code1)

    help_msg = e.value.args[0]
    assert "Version: 1.2.3" in help_msg
    assert "Description:" not in help_msg
    assert "--this-var" not in help_msg
    assert "stuff and things" not in help_msg


def test_docstring(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--help"])

    def code2(this_var: int):  # stuff and things
        """
        this is a description
        """

    with pytest.raises(SystemExit) as e:
        code2.__globals__["__name__"] = "__main__"
        simplecli.wrap(code2)

    help_msg = e.value.args[0]
    assert "Description:" in help_msg
    assert "this is a description" in help_msg
    assert "--this-var" in help_msg
    assert "stuff and things" in help_msg


def test_docstring_tab(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--help"])

    def code2(this_var: int):  # stuff and things
        """
        \t this is a description
        """

    with pytest.raises(ValueError) as e:
        code2.__globals__["__name__"] = "__main__"
        simplecli.wrap(code2)
    assert "tabs are not supported" in str(e.value.args)


@skip_if_uniontype_unsupported
def test_wrap_uniontype(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--help"])

    def code(
        that_var: str | int,  # that is the var
        count: int = 54,  # number of things
    ):
        pass

    with pytest.raises(SystemExit) as e:
        code.__globals__["__name__"] = "__main__"
        simplecli.wrap(code)

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

    code.__globals__["__name__"] = "__main__"
    simplecli.wrap(code)
    (out, _) = capfd.readouterr()
    assert out.strip() == "6.5"

import pytest
import re
import sys
import typing
from simplecli import simplecli


@pytest.fixture(autouse=True)
def ensure_wrapped_not_flagged():
    simplecli._wrapped = False


class PatchGlobal:
    def __init__(
        self,
        func: typing.Callable,
        name: str,
        value: str,
    ) -> None:
        self.func = func
        self.name = name
        self.value = value
        self._no_actual_value = False

    def __enter__(self) -> "PatchGlobal":
        if self.name not in self.func.__globals__:
            self._no_actual_value = True
        else:
            self.actual_value = self.func.__globals__.get(self.name)
        self.func.__globals__[self.name] = self.value
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> "PatchGlobal":
        if self._no_actual_value:
            self.func.__globals__.pop(self.name)
        else:
            self.func.__globals__[self.name] = self.actual_value
        return self


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

    with (
        PatchGlobal(code1, "__name__", "__main__"),
        pytest.raises(SystemExit) as e,
    ):
        simplecli.wrap(code1)

    help_msg = e.value.args[0]
    assert re.search(r"--this-var", help_msg)
    assert re.search(r"\(int\)", help_msg)
    assert re.search(r"stuff and things", help_msg)


def test_wrap_help_complex(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--help"])

    def code(
        that_var: typing.Union[str, int],  # that is the var
        not_this_var: typing.Optional[str],
        count: int = 54,  # number of things
    ):
        pass

    with (
        PatchGlobal(code, "__name__", "__main__"),
        pytest.raises(SystemExit) as e,
    ):
        simplecli.wrap(code)

    help_msg = e.value.args[0]
    assert re.search(r"--that-var", help_msg)
    assert re.search(r"\[str, int\]", help_msg)
    assert re.search(r"that is the var", help_msg)
    assert re.search(r"--count", help_msg)
    assert re.search(r"Default: 54", help_msg)
    assert re.search(r"OPTIONAL", help_msg)


def test_wrap_simple_type_error(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "123", "foo"])

    def code(a: int):
        pass

    with (
        PatchGlobal(code, "__name__", "__main__"),
        pytest.raises(SystemExit, match="Too many positional"),
    ):
        simplecli.wrap(code)


def test_wrap_simple_value_error(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "foo"])

    def code(a: int):
        pass

    with (
        PatchGlobal(code, "__name__", "__main__"),
        pytest.raises(SystemExit, match="must be of type int"),
    ):
        simplecli.wrap(code)


def test_wrap_version_absent(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--version"])

    def code2(this_var: int):  # stuff and things
        pass

    with (
        PatchGlobal(code2, "__name__", "__main__"),
        pytest.raises(SystemExit) as e,
    ):
        simplecli.wrap(code2)

    help_msg = e.value.args[0]
    assert not re.search(r"Description:", help_msg)
    assert not re.search(r"Version: 1.2.3", help_msg)
    assert re.search(r"--this-var", help_msg)
    assert re.search(r"\(int\)", help_msg)
    assert re.search(r"stuff and things", help_msg)


def test_wrap_version_exists(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--version"])

    def code1(this_var: int):  # stuff and things
        pass

    with (
        PatchGlobal(code1, "__version__", "1.2.3"),
        PatchGlobal(code1, "__name__", "__main__"),
        pytest.raises(SystemExit) as e,
    ):
        simplecli.wrap(code1)

    help_msg = e.value.args[0]
    assert re.search(r"Version: 1.2.3", help_msg)
    assert not re.search(r"Description:", help_msg)
    assert not re.search(r"--this-var", help_msg)
    assert not re.search(r"\(int\)", help_msg)
    assert not re.search(r"stuff and things", help_msg)


def test_docstring(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["filename", "--help"])

    def code2(this_var: int):  # stuff and things
        """
        this is a description
        """

    with (
        PatchGlobal(code2, "__name__", "__main__"),
        pytest.raises(SystemExit) as e,
    ):
        simplecli.wrap(code2)

    help_msg = e.value.args[0]
    assert re.search(r"Description:", help_msg)
    assert re.search(r"this is a description", help_msg)
    assert re.search(r"--this-var", help_msg)
    assert re.search(r"\(int\)", help_msg)
    assert re.search(r"stuff and things", help_msg)

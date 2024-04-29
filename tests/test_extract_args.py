from simplecli import simplecli
from textwrap import dedent
# from typing import Optional


def test_emtpy():
    args = simplecli.extract_args(
        tokens=simplecli.tokenize_string(
            "@simplecli.wrap\ndef main():\n    pass"
        ),
        hints={},
    )
    assert args == []


def test_emtpy_with_comment():
    args = simplecli.extract_args(
        tokens=simplecli.tokenize_string(
            "@simplecli.wrap\ndef main():  # wut\n    pass"
        ),
        hints={},
    )
    assert args == []


def test_integer_with_default_oneline():
    function_source = dedent(""" \
        @simplecli.wrap
        def main(foo: int = 123):
            pass""")
    args = simplecli.extract_args(
        tokens=simplecli.tokenize_string(function_source),
        hints={"foo": int},
    )
    expected_arg = simplecli.Arg(
        name="foo",
        line="def main(foo: int = 123):\n",
        raw_datatype=int,
    )
    assert args == [expected_arg]

    # Fails due to oneline misfiring
    assert args[0].default == 123


def test_boolean_with_default():
    function_source = dedent("""\
        @simplecli.wrap
        def main(
            foo: bool = True
        ):
            pass""")
    args = simplecli.extract_args(
        tokens=simplecli.tokenize_string(function_source),
        hints={"foo": bool},
    )
    expected_arg = simplecli.Arg(
        name="foo",
        line="    foo: bool = True\n",
        raw_datatype=bool,
    )
    assert args == [expected_arg]
    assert args[0].default is True
    assert args[0].required is False  # Has no default value
    assert args[0].optional is False  # Flagged as Optional[...]


def test_string_with_inline_comment():
    function_source = dedent("""\
        @simplecli.wrap
        def main(
            bar: str  # input for bar
        ):
            pass""")
    args = simplecli.extract_args(
        tokens=simplecli.tokenize_string(function_source),
        hints={"bar": str},
    )
    expected_arg = simplecli.Arg(
        name="bar",
        line="    bar: str  # input for bar\n",
        raw_datatype=str,
    )
    assert args == [expected_arg]
    assert args[0].default is None
    assert args[0].description == "input for bar"


def test_string_with_prepended_comment():
    function_source = dedent("""\
        @simplecli.wrap
        def main(
            # input for bar
            bar: str
        ):
            pass""")
    args = simplecli.extract_args(
        tokens=simplecli.tokenize_string(function_source),
        hints={"bar": str},
    )
    expected_arg = simplecli.Arg(
        name="bar",
        line="    # input for bar\n    bar: str\n",
        raw_datatype=str,
    )
    assert args == [expected_arg]
    assert args[0].default is None
    assert args[0].description == "input for bar"


def test_int_with_oneline_comment():
    function_source = dedent(""" \
        @simplecli.wrap
        def main(foo_bar: int = 10):  # testfoo 123
            pass""")
    args = simplecli.extract_args(
        tokens=simplecli.tokenize_string(function_source),
        hints={"foo_bar": int},
    )
    expected_arg = simplecli.Arg(
        name="foo_bar",
        line="def main(foo_bar: int = 10):  # testfoo 123\n",
        raw_datatype=int,
    )
    assert args == [expected_arg]
    assert args[0].default == 10
    assert args[0].description == "testfoo 123"


def test_float_with_oneline_comment():
    function_source = dedent(""" \
        @simplecli.wrap
        def main(pi: float = 3.1415):  # It's Pi
            pass""")
    args = simplecli.extract_args(
        tokens=simplecli.tokenize_string(function_source),
        hints={"pi": float},
    )
    expected_arg = simplecli.Arg(
        name="pi",
        line="def main(pi: float = 3.1415):  # It's Pi\n",
        raw_datatype=float,
    )
    assert args == [expected_arg]
    assert args[0].default == 3.1415
    assert args[0].description == "It's Pi"


def test_str_optional_implied_none():
    function_source = dedent("""\
        @simplecli.wrap
        def main(
            quux: Optional[str]
        ):
            pass""")
    args = simplecli.extract_args(
        tokens=simplecli.tokenize_string(function_source),
        hints={"quux": int},
    )
    expected_arg = simplecli.Arg(
        name="quux",
        line="    quux: Optional[str]\n",
        raw_datatype=int,
    )
    assert args == [expected_arg]
    assert args[0].default is None
    assert args[0].required is False  # Has no default value
    assert args[0].optional is True


def test_str_optional_implied_none_with_comment():
    function_source = dedent("""\
        @simplecli.wrap
        def main(
            quux: Optional[str]  # Might be important
        ):
            pass""")
    args = simplecli.extract_args(
        tokens=simplecli.tokenize_string(function_source),
        hints={"quux": int},
    )
    expected_arg = simplecli.Arg(
        name="quux",
        line="    quux: Optional[str]  # Might be important\n",
        raw_datatype=int,
    )
    assert args == [expected_arg]
    assert args[0].default is None
    assert args[0].required is False  # Has no default value
    assert args[0].optional is True


def test_complex_with_heredoc():
    function_source = dedent('''\
        @simplecli.wrap
        def main(
            """
            This function does things
            """
            foo: int,
            quux: Optional[str],
            bar: str = "testing",  # Only change if necessary
        ):
            pass''')
    args = simplecli.extract_args(
        tokens=simplecli.tokenize_string(function_source),
        hints={
            "foo": int,
            "quux": str,
            "bar": str,
        },
    )
    
    assert args == [
        simplecli.Arg(
            name="foo",
            line="    foo: int,\n",
            raw_datatype=int,
        ),
        simplecli.Arg(
            name="quux",
            line="    quux: Optional[str],\n",
            raw_datatype=str,
        ),
        simplecli.Arg(
            name="bar",
            line='    bar: str = "testing",  # Only change if necessary\n',
            raw_datatype=str,
        ),
    ]
    assert args[0].default is None
    assert args[0].required is True
    assert args[0].optional is False
    assert args[0].description == ""

    assert args[1].default is None
    assert args[1].required is False
    assert args[1].optional is True
    assert args[1].description == ""

    assert args[2].default == "testing"
    assert args[2].required is False
    assert args[2].optional is False
    assert args[2].description == "Only change if necessary"

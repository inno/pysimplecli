import typing
from simplecli import simplecli


def test_emtpy():
    def code():
        pass

    args = simplecli.extract_code_args(code)
    assert args == []


def test_emtpy_with_comment():
    def code():  # wut
        pass

    args = simplecli.extract_code_args(code)
    assert args == []


def test_integer_with_default_oneline():
    def code(foo: int = 123):
        pass

    args = simplecli.extract_code_args(code)
    expected_arg = simplecli.Arg(
        name="foo",
        line="    def code(foo: int = 123):\n",
        raw_datatype=int,
        default=123,
    )
    assert args == [expected_arg]


def test_boolean_with_default():
    def code(
        foo: bool = True
    ):
        pass

    args = simplecli.extract_code_args(code)
    expected_arg = simplecli.Arg(
        name="foo",
        line="        foo: bool = True\n",
        raw_datatype=bool,
        default=True,
        required=False,
        optional=False,
    )
    assert args == [expected_arg]


def test_string_with_inline_comment():
    def code(
        bar: str  # input for bar
    ):
        pass

    args = simplecli.extract_code_args(code)
    expected_arg = simplecli.Arg(
        name="bar",
        line="        bar: str  # input for bar\n",
        raw_datatype=str,
        default=None,
        required=True,
        optional=False,
    )
    assert args == [expected_arg]
    assert args[0].description == "input for bar"


def test_string_with_prepended_comment():
    def code(
        # input for bar
        bar: str
    ):
        pass

    args = simplecli.extract_code_args(code)
    expected_arg = simplecli.Arg(
        name="bar",
        line="        # input for bar\n        bar: str\n",
        raw_datatype=str,
        default=None,
    )
    assert args == [expected_arg]
    assert args[0].description == "input for bar"


def test_int_with_oneline_comment():
    def code(foo_bar: int = 10):  # testfoo 123
        pass

    args = simplecli.extract_code_args(code)
    expected_arg = simplecli.Arg(
        name="foo_bar",
        line="    def code(foo_bar: int = 10):  # testfoo 123\n",
        raw_datatype=int,
        default=10,
    )
    assert args == [expected_arg]
    assert args[0].description == "testfoo 123"


def test_float_with_oneline_comment():
    def code(pi: float = 3.1415):  # It's Pi
        pass

    args = simplecli.extract_code_args(code)
    expected_arg = simplecli.Arg(
        name="pi",
        line="    def code(pi: float = 3.1415):  # It's Pi\n",
        raw_datatype=float,
        default=3.1415,
    )
    assert args == [expected_arg]
    assert args[0].description == "It's Pi"


def test_str_optional_implied_none():
    def code(
        quux: typing.Optional[str]
    ):
        pass

    args = simplecli.extract_code_args(code)
    expected_arg = simplecli.Arg(
        name="quux",
        line="        quux: typing.Optional[str]\n",
        raw_datatype=typing.Optional[str],
        default=None,
        required=False,
        optional=True,
    )
    assert args == [expected_arg]


def test_str_optional_implied_none_with_comment():
    def code(
        quux: typing.Optional[str]  # Might be important
    ):
        pass

    args = simplecli.extract_code_args(code)
    expected_arg = simplecli.Arg(
        name="quux",
        line="        quux: typing.Optional[str]  # Might be important\n",
        raw_datatype=typing.Optional[str],
        default=None,
        required=False,
        optional=True,
    )
    assert args == [expected_arg]


def test_complex_with_heredoc():
    def code(
        foo: int,
        quux: typing.Optional[str],
        bar: str = "testing",  # Only change if necessary
    ):
        """
        This function does things
        """
        pass

    args = simplecli.extract_code_args(code)
    assert args == [
        simplecli.Arg(
            name="foo",
            line="        foo: int,\n",
            raw_datatype=int,
            default=None,
            required=True,
            optional=False,
        ),
        simplecli.Arg(
            name="quux",
            line="        quux: typing.Optional[str],\n",
            raw_datatype=typing.Optional[str],
            default=None,
            required=False,
            optional=True,
        ),
        simplecli.Arg(
            name="bar",
            line='        bar: str = "testing",  # Only change if necessary\n',
            raw_datatype=str,
            default="testing",
            required=False,
            optional=False,
        ),
    ]
    assert args[0].description == ""
    assert args[1].description == ""
    assert args[2].description == "Only change if necessary"


def test_integer_with_variable_oneline():
    value = 321

    def code(foo: int = value):
        pass

    args = simplecli.extract_code_args(code)
    expected_arg = simplecli.Arg(
        name="foo",
        line="    def code(foo: int = value):\n",
        raw_datatype=int,
        default=321,
    )
    assert args == [expected_arg]

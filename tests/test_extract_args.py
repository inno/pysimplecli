import typing
from simplecli import simplecli


def test_emtpy():
    def code():
        pass

    params = simplecli.extract_code_params(code)
    assert params == []


def test_emtpy_with_comment():
    def code():  # wut
        pass

    params = simplecli.extract_code_params(code)
    assert params == []


def test_integer_with_default_oneline():
    def code(foo: int = 123):
        pass

    params = simplecli.extract_code_params(code)
    expected_param = simplecli.Param(
        name="foo",
        annotation=int,
        default=123,
    )
    expected_param.set_line("    def code(foo: int = 123):\n")
    assert params == [expected_param]


def test_boolean_with_default():
    def code(
        foo: bool = True
    ):
        pass

    params = simplecli.extract_code_params(code)
    expected_param = simplecli.Param(
        name="foo",
        line="        foo: bool = True\n",
        annotation=bool,
        default=True,
        required=False,
        optional=False,
    )
    assert params == [expected_param]


def test_string_with_inline_comment():
    def code(
        bar: str  # input for bar
    ):
        pass

    params = simplecli.extract_code_params(code)
    assert params == [
        simplecli.Param(
            name="bar",
            description="input for bar",
            annotation=str,
            required=True,
            optional=False,
        )
    ]
    assert params == [
        simplecli.Param(
            name="bar",
            description="input for bar",
            annotation=str,
        )
    ]
    assert params != [
        simplecli.Param(
            name="bar",
            annotation=str,
        )
    ]


def test_string_with_prepended_comment():
    def code(
        # input for bar
        bar: str
    ):
        pass

    params = simplecli.extract_code_params(code)
    expected_param = simplecli.Param(
        name="bar",
        annotation=str,
        required=True,
        description="input for bar"
    )
    assert params == [expected_param]


def test_int_with_oneline_comment():
    def code(foo_bar: int = 10):  # testfoo 123
        pass

    params = simplecli.extract_code_params(code)
    expected_param = simplecli.Param(
        name="foo_bar",
        description="testfoo 123",
        annotation=int,
        default=10,
        required=False,
    )
    assert params == [expected_param]


def test_float_with_oneline_comment():
    def code(pi: float = 3.1415):  # It's Pi
        pass

    params = simplecli.extract_code_params(code)
    expected_param = simplecli.Param(
        name="pi",
        description="It's Pi",
        annotation=float,
        default=3.1415,
        required=False,
    )
    assert params == [expected_param]


def test_str_optional_implied_none():
    def code(
        quux: typing.Optional[str]
    ):
        pass

    params = simplecli.extract_code_params(code)
    expected_param = simplecli.Param(
        name="quux",
        annotation=typing.Optional[str],
        required=False,
        optional=True,
    )
    assert params == [expected_param]


def test_str_optional_implied_none_with_comment():
    def code(
        quux: typing.Optional[str]  # Might be important
    ):
        pass

    params = simplecli.extract_code_params(code)
    expected_param = simplecli.Param(
        name="quux",
        line="        quux: typing.Optional[str]  # Might be important\n",
        annotation=typing.Optional[str],
        required=False,
        optional=True,
    )
    assert params == [expected_param]


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

    params = simplecli.extract_code_params(code)
    assert params == [
        simplecli.Param(
            name="foo",
            annotation=int,
            required=True,
            optional=False,
        ),
        simplecli.Param(
            name="quux",
            annotation=typing.Optional[str],
            required=False,
            optional=True,
        ),
        simplecli.Param(
            name="bar",
            annotation=str,
            description="Only change if necessary",
            default="testing",
            required=False,
            optional=False,
        ),
    ]


def test_integer_with_variable_oneline():
    value = 321

    def code(foo: int = value):
        pass

    params = simplecli.extract_code_params(code)
    expected_param = simplecli.Param(
        name="foo",
        line="    def code(foo: int = value):\n",
        annotation=int,
        default=321,
    )
    assert params == [expected_param]


def test_multiline_offset():
    def code(foo: int,
             bar: int):
        pass

    params = simplecli.extract_code_params(code)
    assert params == [
        simplecli.Param(
            name="foo",
            annotation=int,
        ),
        simplecli.Param(
            name="bar",
            annotation=int,
        )
    ]


def test_multiline_offset_default():
    def code(foo: int,
             bar: int = 567):
        pass

    params = simplecli.extract_code_params(code)
    assert params == [
        simplecli.Param(
            name="foo",
            annotation=int,
        ),
        simplecli.Param(
            name="bar",
            annotation=int,
            default=567,
        )
    ]


def test_multiline_comment_offset():
    def code(foo: int,  # stuff
             bar: int):
        pass

    params = simplecli.extract_code_params(code)
    assert params == [
        simplecli.Param(
            name="foo",
            annotation=int,
            description="stuff",
        ),
        simplecli.Param(
            name="bar",
            annotation=int,
        )
    ]


def test_multiline_comment_offset_multiple():
    def code(foo: int,  # stuff
             # things
             bar: int):
        pass

    params = simplecli.extract_code_params(code)
    assert params == [
        simplecli.Param(
            name="foo",
            annotation=int,
            description="stuff",
        ),
        simplecli.Param(
            name="bar",
            annotation=int,
            description="things",
        )
    ]


def test_multiline_comment_offset_multiple_inline():
    def code(foo: int,  # stuff
             bar: int   # more stuff
             ):
        pass

    params = simplecli.extract_code_params(code)
    assert params == [
        simplecli.Param(
            name="foo",
            annotation=int,
            description="stuff",
        ),
        simplecli.Param(
            name="bar",
            annotation=int,
            description="more stuff",
        )
    ]

from simplecli.simplecli import DefaultIfBool, clean_args


def test_clean_args_empty():
    assert clean_args([]) == ([], {})


def test_clean_args_named_value():
    assert clean_args(["--foo=bar"]) == ([], {"foo": "bar"})


def test_clean_args_named_flag():
    assert clean_args(["--quux"]) == (
        [],
        {"quux": DefaultIfBool},
    )


def test_clean_args_single():
    assert clean_args(["-bar", "123"]) == (["-bar", "123"], {})


def test_clean_args_hyphen_to_underscore():
    assert clean_args(["--foo-bar-s=quux"]) == (
        [],
        {"foo_bar_s": "quux"},
    )


def test_clean_args_positional():
    assert clean_args(["foo", "bar"]) == (["foo", "bar"], {})

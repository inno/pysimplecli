from simplecli import simplecli


def test_clean_passed_args_empty():
    assert simplecli.clean_passed_args([]) == {}


def test_clean_passed_args_named_value():
    assert simplecli.clean_passed_args(["--foo=bar"]) == {"foo": "bar"}


def test_clean_passed_args_named_flag():
    assert simplecli.clean_passed_args(["--quux"]) == {
        "quux": simplecli.TrueIfBool,
    }


def test_clean_passed_args_single():
    assert simplecli.clean_passed_args(["-bar 123"]) == {}


def test_clean_passed_args_hyphen_to_underscore():
    assert simplecli.clean_passed_args(["--foo-bar-s=quux"]) == {
        "foo_bar_s": "quux"
    }


def test_clean_passed_args_positional():
    assert simplecli.clean_passed_args(["foo", "bar"]) == {}

import pytest
from simplecli.simplecli import Param, params_to_kwargs


def test_positional():
    p1 = Param(name="testparam1", annotation=str)
    p2 = Param(name="testparam2", annotation=str)
    argdict = params_to_kwargs(
        params=[p1, p2],
        pos_args=["foo", "bar"],
        kw_args={},
    )
    assert argdict == {"testparam1": "foo", "testparam2": "bar"}


def test_keyword():
    p1 = Param(name="testparam1", annotation=str)
    p2 = Param(name="testparam2", annotation=str)
    argdict = params_to_kwargs(
        params=[p1, p2],
        pos_args=[],
        kw_args={"testparam1": "fooo", "testparam2": "barr"},
    )
    assert argdict == {"testparam1": "fooo", "testparam2": "barr"}


def test_required():
    p1 = Param(name="testparam1", annotation=str)
    p2 = Param(name="testparam2", annotation=str, required=True)
    with pytest.raises(TypeError, match="testparam2"):
        params_to_kwargs(
            params=[p1, p2],
            pos_args=[],
            kw_args={"testparam1": "fooo"},
        )


def test_unknown_arg():
    p1 = Param(name="testparam1", annotation=str, required=False)
    with pytest.raises(SystemExit, match="foo") as e:
        params_to_kwargs(
            params=[p1],
            pos_args=[],
            kw_args={"foo": "bar"},
        )
    assert "Unexpected argument" in str(e.value.args)

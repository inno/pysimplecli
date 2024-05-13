import simplecli


@simplecli.wrap
def code(test_id: int, foo: str) -> str:
    if test_id == 1:
        assert foo == "test"
    if test_id == 2:
        assert foo != "test"

    return f"{test_id + 1} {foo}!"

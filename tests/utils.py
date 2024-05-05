import sys
import pytest
from functools import wraps
from typing import Any, Callable


def min_py(major: int, minor: int) -> bool:
    return sys.version_info < (major, minor)


def skip_if_uniontype_unsupported(
    func: Callable[..., Any],
) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        if min_py(3, 10):
            pytest.skip("UnionType requires >= py3.10")
            return None
        return func(*args, **kwargs)

    return wrapper

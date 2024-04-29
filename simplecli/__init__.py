from simplecli.simplecli import run
from collections.abc import Callable
from typing import TypeVar
from typing_extensions import ParamSpec

P = ParamSpec("P")
R = TypeVar("R")


def wrap(func: Callable[P, R]) -> None:
    run("func")

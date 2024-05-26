# pysimplecli

[![codecov](https://codecov.io/gh/inno/pysimplecli/branch/main/graph/badge.svg?token=T6NP6XSKJG)](https://codecov.io/gh/inno/pysimplecli)
[![CI](https://github.com/inno/pysimplecli/actions/workflows/main.yml/badge.svg)](https://github.com/inno/pysimplecli/actions/workflows/main.yml)

Want to turn your script into a command line utility, but don't want the overhead of [argparse](https://docs.python.org/library/argparse.html)?

*You've come to the right place!*

Simply import and wrap whatever function you'd like to expose. That's it!

Function variables are turned into CLI parameters, complete with input validation and help text generated from inline comments.


## Install from PyPI

```bash
pip install pysimplecli
```

## Quick Start

To convert a Python function into a CLI command, simply use the `wrap` decorator from the `simplecli` module. Here is a simple example:


```python
import simplecli


@simplecli.wrap
def main(
    name: str,  # Person to greet
) -> None:
    print(f"Hello, {name}!")
```

```bash
$ python3 myprogram.py --name="Dade Murphy"
Hello, Dade Murphy!
```

That's it!

## Features

### No configuration to worry about

Everything Just Works™ out of the box.

### Autogenerated help

Parameters show up automatically and comments make them more friendly.

```bash
$ python3 hello.py --help
Usage:
  hello.py [name]

Options:
  --name  Person to greet
  --help  Display hello.py version
 ```

### Unicode support

```bash
$ python3 hello.py --name="Donatello 🐢"
Hello, Donatello 🐢!
```

### Cross-platform

Tested on Windows/Linux/Mac with Python >= 3.9.


### Required parameters are also positional

Want to pass positional instead of named parameters? All required parameters are available in top-down order.


```bash
$ python3 hello.py "El Duderino"
Hello, El Duderino!
```
### Autogenerated version parameter

If you have the dunder variable `__version__` set, you get a `--version` parameter.

```python
import simplecli
___version___ = "1.2.3"


@simplecli.wrap
def main(
    name: str,  # Person to greet
) -> None:
    print(f"Hello, {name}!")
```

```bash
$ python3 hello.py --version
hello.py version 1.2.3
```

### Automatic docstring to help description

Want to add some detail to your help output? Just make a docstring in the function that's being wrapped.

```python
import simplecli
__version__ = "1.2.3"


@simplecli.wrap
def main(
    name: str,  # Person to greet
) -> None:
    """
    This is a utility that greets whoever engages it. It's a simple example
    of how to use the `simplecli` utility module. Give it a try!
    """
    print(f"Hello, {name}!")
```

```bash
$ python3 hello.py --help
Usage:
  hello.py [name]

Description:
  This is a utility that greets whoever engages it. It's a simple example
  of how to use the `simplecli` utility module. Give it a try!

Options:
  --name      Person to greet
  --help      Show this message
  --version   Display hello.py version
```

## Gotchas

### "Required" may be a bit confusing

A parameter becomes "required" if it is an `int`, `float` or `str` and does not have a default.

`bool` arguments cannot be required as there are only two possible states. Instead, they are `False` by default and become `True` when passed as a flag.

### Complex variables are not supported

*Only* simple variable types (`bool`, `float`, `int`, `str`) are currently supported as well as `list` and `set` of those types. Mapping types are beyond the scope of this utility.

### Only one `@wrap` allowed per file

With more than one decorator, it's impossible to tell which function you'd like to wrap. Because of this, we enforce a single `@wrap` per file. Importing modules using `pysimplecli` is supported, as is calling said wrapped functions.

### Truth table for boolean parameters

| Parameter Default | Without Argument | With Argument |
| --- | --- | --- |
| `True` | `True` | `False` |
| `False` | `False` | `True` |
| no default | `False` | `True` |

## How It Works

The `wrap` decorator takes the annotated parameters of a given function and maps them to corresponding command-line arguments. It relies heavily on Python's `inspect` and `tokenize` modules to gather parameters, parse comments for parameter descriptions, determine default functionality, etc...  In fact, a core part of this module is a are heavily extended `inspect.Parameter` objects.

## Why not just use `argparse`?

`argparse` is great for advanced input control. Unfortunately, that level of control means considerably more overhead for simple utilities. To be clear, this is not intended to replace `argparse`. `simplecli` is meant to easily expose a python function as a script.

(I've also felt conflicted about dunder names being used openly in `if __name__ == "__main__":`)


Here's an example of an `argparse` solution
```python
import argparse
import sys
__version__ = "1.2.3"


def add(a: int = 5, b: int = 10) -> None:
    print(a + b)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--a", default=5, required=True, type=int,
                        help="First integer to add")
    parser.add_argument("--b", default=10, required=True, type=int,
                        help="Second integer to add")
    parser.add_argument("--version", action="version",
                        version=f"{sys.argv[0]} version {__version__}")
    args = parser.parse_args()
    add(args.a, args.b)
```

Here's the same example, but with `simplecli`

```python
from simplecli import wrap
__version__ = "1.2.3"


@wrap
def add(
    a: int = 5,  # First integer to add
    b: int = 10,  # Second integer to add
) -> None:
    print(a + b)
```


## Contributing

Feel free to [open an issue](../../issues/new) and [create a pull request](../../pulls)!

## License

pysimplecli © 2024 by Clif Bratcher is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

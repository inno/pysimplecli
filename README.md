# pysimplecli

[![codecov](https://codecov.io/gh/inno/pysimplecli/branch/main/graph/badge.svg?token=T6NP6XSKJG)](https://codecov.io/gh/inno/pysimplecli)
[![CI](https://github.com/inno/pysimplecli/actions/workflows/main.yml/badge.svg)](https://github.com/inno/pysimplecli/actions/workflows/main.yml)

Want to turn your script into a command line utility, but don't want the
overhead of [argparse](https://docs.python.org/3/library/argparse.html)?

You've come to the right place!

Simply import and wrap whatever function you'd like to expose. That's it!

Function variables are turned into CLI parameters, complete with input
validation and help text generated from inline comments.

Note that only simple variable types (`bool`, `float`, `int`, `str`) are
currently supported. Mapping and sequence types might be supported in the
future.

## Features

- **Function-to-CLI Conversion**: Easily turn Python functions into command-line tools using the `wrap` decorator.
- **Intelligent Argument Parsing**: Automatically parse command-line arguments to match the function parameters, including type handling.
- **Enhanced Decorator**: Includes parameter details such as descriptions from inline comments next to parameter definitions, providing richer help text and usage messages.
- **Automatic Argument Parsing**: Parameters of the function are automatically mapped to command-line arguments, including type conversion.
- **Comments as Help Text**: Inline comments are used as help text in the generated interface, providing context and guidance directly from code.


## Install from PyPI

You can install pysimplecli directly from source as follows:

```bash
pip install pysimplecli
pip install git+https://github.com/inno/pysimplecli.git
```

## Quick Start

To convert a Python function into a CLI command, simply use the `wrap` decorator from the `simplecli` module. Here is how you can get started:

```python
import simplecli


@simplecli.wrap
def main(
    name: str,  # Person to greet
):
    print(f"Hello, {name}!")
```

```bash
$ python3 myprogram.py --name="Dade Murphy"
Hello, Dade Murphy!
```

```bash
$ python3 myprogram.py --help
Usage:
  myprogram.py [name]

Options:
  --name  Person to greet
  --help  This message
 ```

## How It Works

The `wrap` decorator takes the annotated parameters of a given function and maps them to corresponding command-line arguments. It uses Python's introspection features and the `tokenize` module to parse inline comments for parameter descriptions, enriching the auto-generated help output.

## Why not just use `argparse`?

`argparse` is great for advanced input control. Unfortunately, that level of control means considerably more overhead for simple utilities. To be clear, this is not intended to replace `argparse`. `simplecli` is meant to easily expose a python function as a script.

(I've also felt conflicted about dunder names being used openly in `if __name__ == "__main__":`)


Here's an example of an `argparse` solution
```python
import argparse


def add(a: int = 5, b: int = 10):
    print(a + b)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--a", default=5, required=True, type=int,
                        help="First integer to add")
    parser.add_argument("--b", default=10, required=True, type=int,
                        help="Second integer to add")
    args = parser.parse_args()
    add(args.a, args.b)
```

Here's the same example, but with `simplecli`

```python
from simplecli import wrap


@wrap
def add(
    a: int = 5,  # First integer to add
    b: int = 10,  # Second integer to add
):
    print(a + b)
```


## Contributing

Feel free to [open an issue](./issues/new) and [create a pull request](./pulls)!

## License

pysimplecli © 2024 by Clif Bratcher is licensed under [CC BY 4.0][https://creativecommons.org/licenses/by/4.0/]

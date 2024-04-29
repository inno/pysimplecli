# pysimplecli

[![codecov](https://codecov.io/gh/inno/pysimplecli/branch/main/graph/badge.svg?token=project_urlname_token_here)](https://codecov.io/gh/inno/pysimplecli)
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

## Install from PyPI

```bash
pip install pysimplecli
```

## Usage

```py
import simplecli


@simplecli.wrap
def main(
    name: str,  # Your name here
):
    print(f"Hello, {name}!")
```

```bash
python3 myprogram.py --name="My Name Here"
```

```bash
python3 myprogram.py --help
```

## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.

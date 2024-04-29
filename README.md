# pysimplecli

pysimplecli is a Python utility module designed to transform any function into a command-line executable by using a powerful `wrap` decorator. This decorator intelligently parses function parameters and their annotations to generate command-line arguments automatically.

## Features

- **Function-to-CLI Conversion**: Easily turn Python functions into command-line tools using the `wrap` decorator.
- **Intelligent Argument Parsing**: Automatically parse command-line arguments to match the function parameters, including type handling.
- **Enhanced Decorator**: Includes parameter details such as descriptions from inline comments next to parameter definitions, providing richer help text and usage messages.
- **Automatic Argument Parsing**: Parameters of the function are automatically mapped to command-line arguments, including type conversion.
- **Comments as Help Text**: Inline comments are used as help text in the generated interface, providing context and guidance directly from code.


## Installation

You can install pysimplecli directly from source as follows:

```bash
pip install pysimplecli
pip install git+https://github.com/inno/pysimplecli.git
```

## Quick Start

To convert a Python function into a CLI command, simply use the `wrap` decorator from the `simplecli` module. Here is how you can get started:

```python
from simplecli import wrap

@wrap
def main(greeting: str, count: int = 1):
    """ Greets the user a specified number of times. """
    for _ in range(count):
        print(greeting)
```

This function can then be executed from the command line like this:

```bash
python script.py --greeting "Hello, World!" --count 3
```

## How It Works

The `wrap` decorator processes the annotated parameters of your function and maps them to corresponding command-line arguments. It uses Python's introspection features and the `tokenize` module to parse inline comments for parameter descriptions, enriching the auto-generated help output.

### Advanced Usage

Here’s an example of a function with both optional and required parameters, demonstrating how descriptions are parsed:

```python
from simplecli import wrap

@wrap
def process_data(file_path: str, verbose: bool = False):
    """ Process data from a specified file path. """
    if verbose:
        print("Verbose mode enabled.")
    with open(file_path, 'r') as file:
        print("Data processed.")

if __name__ == "__main__":
    process_data()
```

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
    parser.add_argument("--a", default=5, required=True, type=int)
    parser.add_argument("--b", default=10, required=True, type=int)
    args = parser.parse_args()
    add(args.a, args.b)
```

Here's the same example, but with `simplecli`

```python
from simplecli import wrap


@wrap
def add(a: int = 5, b: int = 10):
    print(a + b)
```



## Contributing

Contributions to pysimplecli are welcome! Feel free to fork the repository, make improvements, and submit pull requests. We appreciate all contributions, from feature enhancements to documentation improvements.

## License

pysimplecli is open-sourced under the MIT License.

import contextlib
import inspect
import io
import re
import sys
import tokenize
from collections import OrderedDict
from collections.abc import Generator
from typing import (
    Any,
    Callable,
    Union,
    get_args,
    get_origin,
)


# 2023 - Clif Bratcher WIP


# Overloaded placeholder for a potential boolean
TrueIfBool = "Crazy going slowly am I, 6, 5, 4, 3, 2, 1, switch!"

ArgDict = dict[str, Union[bool, str]]
ValueType = Union[bool, float, int, str]


class Param(inspect.Parameter):
    required: bool = True
    optional: bool = False
    description: str = ""

    def __init__(self, *argv: Any, **kwargs: Any) -> None:
        if "kind" not in kwargs:
            kwargs["kind"] = inspect.Parameter.POSITIONAL_OR_KEYWORD

        param_line = str(kwargs.pop("line", ""))
        param_required = bool(kwargs.pop("required", True))
        param_optional = bool(kwargs.pop("optional", False))
        super().__init__(*argv, **kwargs)
        self.required = param_required
        self.optional = param_optional
        self.set_line(param_line)

    @property
    def help_name(self) -> str:
        return self.name.replace("_", "-")

    def _set_description(self, line: str) -> None:
        self.description = re.sub(r"^#\s+", "", line.lstrip()).strip()

    def set_line(self, line: str) -> None:
        self.description = ""
        valid_tokens = (tokenize.NAME, tokenize.NUMBER, tokenize.STRING)
        tokens = list(
            tokenize.generate_tokens(io.StringIO(line).readline),
        )
        # Filter out cruft
        tokens = [t for t in tokens if t.type in valid_tokens]
        for token in tokens:
            if token.string == "Optional":
                self.required = False
                self.optional = True
        if self.default is not inspect._empty:
            self.required = False

        for token in tokenize_string(line):
            if token.exact_type == tokenize.COMMENT:
                self._set_description(token.string)

    @property
    def datatypes(self) -> list[type]:
        args = get_args(self.annotation)
        if args:
            return list(args)
        elif isinstance(self.annotation, list):
            return self.annotation
        return [self.annotation]

    def validate(self, value: ValueType) -> bool:
        passed = False
        for expected_type in self.datatypes:
            try:
                expected_type(value)
                passed = True
                break
            except ValueError:
                pass
        return passed


def tokenize_string(string: str) -> Generator[tokenize.TokenInfo, None, None]:
    return tokenize.generate_tokens(io.StringIO(string).readline)


def help_text(filename: str, args: list[Param], docstring: str = "") -> None:
    # XXX build list of arguments for 'usage'
    print(f"Usage: \n\t{filename} ...\n")
    if docstring:
        print(f"Description: \n{docstring}\n")
    print("Options:")
    for arg in args:
        if get_origin(arg.annotation) is Union:
            types = [a.__name__ for a in get_args(arg.annotation)]
            if "NoneType" in types:
                types.remove("NoneType")
                arg_types = " ".join(types)
                arg_types += " OPTIONAL"
        else:
            arg_types = arg.annotation.__name__
        print(f" --{arg.help_name}\t\t({arg_types})\t{arg.description}")


def clean_passed_args(argv: list[str]) -> ArgDict:
    passed_args: ArgDict = {}
    in_single = False  # Maintain state as single is per-record
    previous_single = ""
    for passed_arg in argv:
        double_hyphen = re.match(r"--([\w-]+)(?:=(.+))?", passed_arg)
        single_hyphen = re.match(r"-([\w-]+)", passed_arg)
        if double_hyphen:
            in_single = False
            value = double_hyphen.groups()[1]
            # XXX Bug for non-boolean values. This
            if value is None:
                value = TrueIfBool
            # Translate hyphens to underscores
            passed_args[double_hyphen.groups()[0].replace("-", "_")] = value
        elif single_hyphen:
            in_single = True
            previous_single = single_hyphen.groups()[0].replace("-", "_")
            # Assume single is boolean (may bite us if default is `False`)
            passed_args[previous_single] = True
        elif in_single:
            in_single = False
            passed_args[previous_single] = passed_arg
        else:
            print(f"wut: '{passed_arg}'")
        # XXX positional based on required args
    return passed_args


def process_arg(arg: Param, passed_args: ArgDict) -> None:
    if arg.name in passed_args:
        if arg.validate(passed_args[arg.name]) is False:
            print(f"Error: argument '{arg.help_name}' has an invalid value")
            # XXX Display the expected info?
            exit()
        # Handle datatypes
        type_args = get_args(arg.annotation)
        if not type_args:
            if passed_args[arg.name] is TrueIfBool:
                if arg.annotation is not bool:
                    print(
                        f"Error: argument '{arg.help_name}' requires a value"
                    )
                    exit()
                else:
                    passed_args[arg.name] = True
            passed_args[arg.name] = arg.annotation(passed_args[arg.name])
            return
        for type_arg in type_args:
            with contextlib.suppress(TypeError):
                passed_args[arg.name] = type_arg(passed_args[arg.name])
        return
    if arg.required is True:
        print(f"Error: argument '{arg.help_name}' is required!")
        exit()


def parse_args(
    args: list[Param],
    docstring: str = "",
) -> ArgDict:
    filename = sys.argv[0]
    argv = sys.argv[1:]

    passed_args = clean_passed_args(argv)
    if "help" in passed_args or "h" in passed_args:
        help_text(filename, args, docstring)
        exit()

    for arg in args:
        process_arg(arg, passed_args)

    for k, _ in passed_args.items():
        if k not in [a.name for a in args]:
            print(f"Error: Unexpected argument '{k}'")
            exit()

    return passed_args


def format_docstring(docstring: str) -> str:
    # "Spaces are the preferred indentation method."
    # https://peps.python.org/pep-0008/#tabs-or-spaces
    docstring = docstring.rstrip()
    match = re.match(r"^\s*", docstring)
    if not match:
        return docstring
    return re.sub(
        " " * (match.span()[1] - 1),
        "",
        docstring,
        flags=re.MULTILINE,
    )


def wrap(func: Callable[..., Any]) -> None:
    args = extract_code_args(code=func)
    docstring = func.__doc__ or ""
    clean_args = parse_args(
        args=args,
        docstring=format_docstring(docstring),
    )
    func(**clean_args)


def extract_code_args(code: Callable[..., Any]) -> list[Param]:
    tokens = tokenize_string(inspect.getsource(code))
    signature = inspect.signature(code)
    params = OrderedDict(
        (
            k,
            Param(
                name=v.name,
                default=v.default,
                annotation=v.annotation,
                kind=v.kind,
            ),
        )
        for k, v in signature.parameters.items()
    )
    hints = {k: v.annotation for k, v in params.items()}
    attrs = hints.copy()
    # We don't care about the return value of the entrypoint
    if "return" in attrs:
        attrs.pop("return")
    args: list[Param] = []

    prepended_comment = ""

    while attrs:
        token = next(tokens)
        if token.exact_type == tokenize.COMMENT:
            prepended_comment = token.line
        elif token.exact_type == tokenize.NAME:
            if token.string in attrs:
                attrs.pop(token.string)
                param = params[token.string]
                param.set_line(token.line)
                if prepended_comment:
                    param._set_description(prepended_comment)
                args.append(param)
                prepended_comment = ""
    return args

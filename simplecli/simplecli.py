import contextlib
import inspect
import io
import re
import sys
import tokenize
from dataclasses import dataclass
from collections.abc import Generator
from types import MappingProxyType
from typing import (
    Any,
    Callable,
    Optional,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

# 2023 - Clif Bratcher WIP


# Overloaded placeholder for a potential boolean
TrueIfBool = "Crazy going slowly am I, 6, 5, 4, 3, 2, 1, switch!"

ArgList = dict[str, Union[bool, str]]
ValueType = Union[bool, float, int, str]


@dataclass
class Arg:
    name: str
    line: str
    raw_datatype: Any
    required: bool = True
    optional: bool = False
    default: Optional[ValueType] = None

    def __post_init__(self) -> None:
        valid_tokens = (tokenize.NAME, tokenize.NUMBER, tokenize.STRING)
        tokens = list(
            tokenize.generate_tokens(io.StringIO(self.line).readline),
        )

        # Filter out cruft
        tokens = [t for t in tokens if t.type in valid_tokens]
        for token in tokens:
            if token.string == "Optional":
                self.required = False
                self.optional = True
        if self.default is not None:
            self.required = False

    @property
    def datatypes(self) -> list[type]:
        # XXX May need 'Union' handling as well
        args = get_args(self.raw_datatype)
        if args:
            return list(args)
        elif isinstance(self.raw_datatype, list):
            return self.raw_datatype
        return [self.raw_datatype]

    @property
    def help_name(self) -> str:
        return self.name.replace("_", "-")

    @property
    def description(self) -> str:
        # Re-process inline comments for descriptions
        for token in tokenize_string(self.line):
            if token.exact_type == tokenize.COMMENT:
                return re.sub(r"^#\s+", "", token.string.lstrip())
        return ""

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


def tokenize_code(
    code: Callable[..., Any],
) -> Generator[tokenize.TokenInfo, None, None]:
    return tokenize_string(inspect.getsource(code))


def code_params(
    code: Callable[..., Any],
) -> MappingProxyType[str, inspect.Parameter]:
    return inspect.signature(code).parameters


def help_text(filename: str, args: list[Arg], docstring: str = "") -> None:
    # XXX build list of arguments for 'usage'
    print(f"Usage: \n\t{filename} ...\n")
    if docstring:
        print(f"Description: \n{docstring}\n")
    print("Options:")
    for arg in args:
        if get_origin(arg.raw_datatype) is Union:
            types = [a.__name__ for a in get_args(arg.raw_datatype)]
            if "NoneType" in types:
                types.remove("NoneType")
                arg_types = " ".join(types)
                arg_types += " OPTIONAL"
        else:
            arg_types = arg.raw_datatype.__name__
        print(f" --{arg.help_name}\t\t({arg_types})\t{arg.description}")


def clean_passed_args(argv: list[str]) -> ArgList:
    passed_args: ArgList = {}
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


def process_arg(arg: Arg, passed_args: ArgList) -> None:
    if arg.name in passed_args:
        if arg.validate(passed_args[arg.name]) is False:
            print(f"Error: argument '{arg.help_name}' has an invalid value")
            # XXX Display the expected info?
            exit()
        # Handle datatypes
        type_args = get_args(arg.raw_datatype)
        if not type_args:
            if passed_args[arg.name] is TrueIfBool:
                if arg.raw_datatype is not bool:
                    print(
                        f"Error: argument '{arg.help_name}' requires a value"
                    )
                    exit()
                else:
                    passed_args[arg.name] = True
            passed_args[arg.name] = arg.raw_datatype(passed_args[arg.name])
            return
        for type_arg in type_args:
            with contextlib.suppress(TypeError):
                passed_args[arg.name] = type_arg(passed_args[arg.name])
        return
    if arg.required is True:
        print(f"Error: argument '{arg.help_name}' is required!")
        exit()


def parse_args(
    args: list[Arg],
    docstring: str = "",
) -> ArgList:
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


def run(main_function: str = "main") -> None:
    current_frame = inspect.currentframe()
    if not current_frame:
        print("10001: This shouldn't be possible...")
        exit()
    f_back = current_frame.f_back
    if not f_back:
        print("10002: This shouldn't be possible...")
        exit()
    f_locals = f_back.f_locals
    if main_function not in f_locals:
        print(f"Sorry, I need the '{main_function}' function to build on!")
        exit()
    # Bail if the script is imported instead of called directly
    top_of_stack_file = inspect.stack()[-1].filename
    caller_file = inspect.getfile(f_back)
    # Called as decorator
    if f_back.f_back:
        caller_file = inspect.getfile(f_back.f_back)
    # File not called directly, do not treat as executed
    if top_of_stack_file != caller_file:
        return

    args = extract_code_args(code=f_locals[main_function])
    docstring = f_locals[main_function].__doc__ or ""
    clean_args = parse_args(
        args=args,
        docstring=format_docstring(docstring),
    )
    f_locals[main_function](**clean_args)


def extract_code_args(code: Callable[..., Any]) -> list[Arg]:
    return extract_args(
        tokens=tokenize_code(code),
        hints=get_type_hints(code),
        params=inspect.signature(code).parameters,
    )


def extract_args(
    hints: dict[str, Any],
    tokens: Generator[tokenize.TokenInfo, None, None],
    params: MappingProxyType[str, inspect.Parameter],
) -> list[Arg]:
    attrs = hints.copy()
    # We don't care about the return value of the entrypoint
    if "return" in attrs:
        attrs.pop("return")
    args: list[Arg] = []

    prepended_comment = ""

    # No need to continue processing if we've found everything
    while attrs:
        token = next(tokens)
        if token.exact_type == tokenize.COMMENT:
            prepended_comment = token.line
        elif token.exact_type == tokenize.NAME:
            if token.string in attrs:
                attr_type = attrs.pop(token.string)
                default = params[token.string].default
                if default == inspect._empty:
                    default = None
                args.append(
                    Arg(
                        name=token.string,
                        line=prepended_comment + token.line,
                        raw_datatype=attr_type,
                        default=default,
                    ),
                )
    return args

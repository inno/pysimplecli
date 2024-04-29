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


_wrapped = False
Empty = inspect._empty
# Overloaded placeholder for a potential boolean
TrueIfBool = "Crazy going slowly am I, 6, 5, 4, 3, 2, 1, switch!"

ValueType = Union[bool, float, int, str]
ArgDict = dict[str, ValueType]
ArgList = list[str]


class Param(inspect.Parameter):
    required: bool = True
    optional: bool = False
    description: str = ""
    _value: Any = Empty

    def __init__(self, *argv: Any, **kwargs: Any) -> None:
        if "kind" not in kwargs:
            kwargs["kind"] = inspect.Parameter.POSITIONAL_OR_KEYWORD
        param_description = str(kwargs.pop("description", ""))
        param_line = str(kwargs.pop("line", ""))
        param_required = bool(kwargs.pop("required", True))
        param_optional = bool(kwargs.pop("optional", False))
        super().__init__(*argv, **kwargs)
        self.required = param_required
        self.description = param_description
        self.optional = param_optional
        if not self.description:
            self.set_line(param_line)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Param):
            return NotImplemented
        if (
            self.description != other.description
            or self.default != other.default
            or self.required != other.required
            or self.optional != other.optional
        ):
            return False
        if self._value != Empty or self.default != Empty:
            if other._value != Empty or other.default != Empty:
                if self.value != other.value:
                    return False
        return True

    def __str__(self) -> str:
        return (
            f"{self.name}: "
            f"annotation={self.help_type} "
            f"description='{self.description}' "
            f"default='{self.default}' "
            f"required='{self.required}' "
            f"optional='{self.optional}' "
            f"value='{self.value}'"
        )

    @property
    def help_name(self) -> str:
        return self.name.replace("_", "-")

    @property
    def help_type(self) -> str:
        if isinstance(self.annotation, list):
            return f"[{[a.__name__ for a in self.annotation]}]"
        return self.annotation.__name__

    @property
    def value(self) -> ValueType:
        if self._value != Empty:
            return self._value
        if self.default != Empty:
            return self.default
        print(
            f"Error, empty value and default for {self.help_name}.. "
            "I'm not sure what to do!"
        )
        exit()

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
        if self.default is not Empty:
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

    def set_value(self, value: ValueType) -> None:
        if self.validate(value) is False:
            print(
                f"Error: '{self.help_name}' has an invalid value. "
                f"Please pass a value of type {self.help_type}!"
            )
            exit()
        # Handle datatypes
        args = get_args(self.annotation)
        if not args:
            if value is TrueIfBool:
                if self.annotation is not bool:
                    print(
                        f"Error: argument '{self.help_name}' "
                        "requires a value"
                    )
                    exit()
                else:
                    self._value = self.annotation(True)
                    return
            self._value = self.annotation(value)
            return
        for type_arg in args:
            with contextlib.suppress(TypeError):
                self._value = type_arg(value)


def tokenize_string(string: str) -> Generator[tokenize.TokenInfo, None, None]:
    return tokenize.generate_tokens(io.StringIO(string).readline)


def help_text(filename: str, params: list[Param], docstring: str = "") -> None:
    # XXX build list of arguments for 'usage'
    print(f"Usage: \n\t{filename} ...\n")
    if docstring:
        print(f"Description: \n{docstring}\n")
    print("Options:")
    for arg in params:
        if get_origin(arg.annotation) is Union:
            types = [a.__name__ for a in get_args(arg.annotation)]
            if "NoneType" in types:
                types.remove("NoneType")
                arg_types = " ".join(types)
                arg_types += " OPTIONAL"
        else:
            arg_types = arg.help_name
        print(f" --{arg.help_name}\t\t({arg_types})\t{arg.description}")


def clean_args(argv: list[str]) -> tuple[ArgList, ArgDict]:
    pos_args: ArgList = []
    kw_args: ArgDict = {}
    for arg in argv:
        double_hyphen = re.match(r"--([\w-]+)(?:=(.+))?", arg)
        if double_hyphen:
            value = double_hyphen.groups()[1]
            # XXX Bug for non-boolean values. Also ignores defaults for bool
            if value is None:
                value = TrueIfBool
            # Translate hyphens to underscores
            kw_args[double_hyphen.groups()[0].replace("-", "_")] = value
        else:
            pos_args.append(arg)
    return pos_args, kw_args


def parse_args(
    params: list[Param],
    docstring: str = "",
    filename: str = sys.argv[0],
    argv: list[str] = sys.argv[1:],
) -> ArgDict:
    pos_args, kw_args = clean_args(argv)
    if "help" in kw_args or "h" in kw_args:
        help_text(filename, params, docstring)
        exit()

    missing_params = []

    for param in params:
        # Positional arguments take precedence
        if pos_args:
            param.set_value(pos_args.pop(0))
        elif param.name in kw_args:
            param.set_value(kw_args[param.name])
            continue
        elif param.required:
            missing_params.append(param)
            continue

    if pos_args:
        print("Error, too many positional arguments!")
        exit()

    if missing_params:
        print(
            "Error, missing required "
            f"argument{'s' if len(missing_params) > 1 else ''}:"
        )
        for param in missing_params:
            help_line = f"\t--{param.help_name}\t({param.help_type})"
            if param.description:
                help_line += f" - {param.description}"
            print(help_line)
        exit()

    for k, _ in kw_args.items():
        if k not in [a.name for a in params]:
            print(f"Error: Unexpected argument '{k}'")
            exit()

    return {param.name: param.value for param in params}


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
    global _wrapped
    if _wrapped:
        print("Error, sorry only ONE `@wrap` decorator allowed!")
        exit()
    _wrapped = True
    params = extract_code_params(code=func)
    docstring = func.__doc__ or ""
    kwargs = parse_args(
        params=params,
        docstring=format_docstring(docstring),
    )
    func(**kwargs)


def extract_code_params(code: Callable[..., Any]) -> list[Param]:
    tokens = tokenize_string(inspect.getsource(code))
    signature = inspect.signature(code)
    ordered_params = OrderedDict(
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
    hints = {k: v.annotation for k, v in ordered_params.items()}
    attrs = hints.copy()
    # We don't care about the return value of the entrypoint
    if "return" in attrs:
        attrs.pop("return")
    params: list[Param] = []

    prepended_comment = ""

    param = None

    while attrs:
        token = next(tokens)
        if token.exact_type == tokenize.COMMENT:
            prepended_comment = token.string
        # tokenize.NL -
        # when a logical line of code is continued over multiple lines
        elif token.exact_type == tokenize.NL:
            if param:
                param.set_line(prepended_comment)
                params.append(param)
                prepended_comment = ""
                param = None
            continue
        elif token.exact_type == tokenize.NAME:
            if token.string not in attrs:
                continue
            attrs.pop(token.string)
            param = ordered_params[token.string]
            # Catch in the event a tokenize.NL is coming soon
            try:
                param.set_line(token.line)
            except tokenize.TokenError:
                continue
            if prepended_comment:
                param._set_description(prepended_comment)
            params.append(param)
            prepended_comment = ""
            param = None
    if param:
        params.append(param)

    return params

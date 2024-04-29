import contextlib
import inspect
import io
import re
import sys
from collections import OrderedDict
from collections.abc import Generator
from tokenize import (
    COMMENT,
    NAME,
    NL,
    NUMBER,
    STRING,
    TokenError,
    TokenInfo,
    generate_tokens,
)
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
DefaultIfBool = "Crazy going slowly am I, 6, 5, 4, 3, 2, 1, switch!"

ValueType = Union[type[Empty], bool, float, int, str]
ArgDict = dict[str, ValueType]
ArgList = list[str]


class Param(inspect.Parameter):
    def __init__(self, *argv: Any, **kwargs: Any) -> None:
        if "kind" not in kwargs:
            kwargs["kind"] = inspect.Parameter.POSITIONAL_OR_KEYWORD
        param_description = str(kwargs.pop("description", ""))
        param_line = str(kwargs.pop("line", ""))
        param_value = kwargs.pop("value", Empty)
        param_required = bool(kwargs.pop("required", True))
        param_optional = bool(kwargs.pop("optional", False))
        super().__init__(*argv, **kwargs)
        self._value = param_value
        self.required = param_required
        self.description = param_description
        self.optional = param_optional
        if not self.description:
            self.parse_line(param_line)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Param):
            return NotImplemented
        return (
            self.description == other.description
            and self.default == other.default
            and self.required == other.required
            and self.optional == other.optional
            and self.value == other.value
        )

    def __str__(self) -> str:
        default = "Empty" if self.default is Empty else f"'{self.default}'"
        value = "Empty" if self.value is Empty else f"'{self.value}'"
        return (
            f"{self.name}: "
            f"annotation={self.help_type} "
            f"description='{self.description}' "
            f"default={default} "
            f"required='{self.required}' "
            f"optional='{self.optional}' "
            f"value={value} "
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
        return Empty

    def _set_description(self, line: str) -> None:
        self.description = re.sub(r"^#\s+", "", line.lstrip()).strip()

    def parse_line(self, line: str) -> bool:
        self.description = ""
        try:
            tokens = list(tokenize_string(line))
        except TokenError:
            return False

        for token in tokens:
            if token.type not in (COMMENT, NAME, NUMBER, STRING):
                continue
            if token.exact_type is COMMENT:
                self._set_description(token.string)
            if token.string == "Optional":
                self.required = False
                self.optional = True
        if self.default is not Empty:
            self.required = False
        return True

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
            if value is DefaultIfBool:
                if self.annotation is not bool:
                    print(
                        f"Error: argument '{self.help_name}' "
                        "requires a value"
                    )
                    exit()
                elif self.default != Empty:
                    self._value = self.annotation(self.default)
                    return
                else:
                    self._value = self.annotation(True)
                    return
            self._value = self.annotation(value)
            return
        for type_arg in args:
            with contextlib.suppress(TypeError):
                self._value = type_arg(value)


def tokenize_string(string: str) -> Generator[TokenInfo, None, None]:
    return generate_tokens(io.StringIO(string).readline)


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
        if not double_hyphen:
            pos_args.append(arg)
            continue
        value = double_hyphen.groups()[1]
        if value is None:
            value = DefaultIfBool
        # Translate hyphens to underscores
        kw_args[double_hyphen.groups()[0].replace("-", "_")] = value
    return pos_args, kw_args


def check_for_unexpected_args(params: list[Param], kw_args: ArgDict) -> None:
    for k, _ in kw_args.items():
        if k not in [a.name for a in params]:
            print(f"Error: Unexpected argument '{k}'")
            exit()


def missing_params_msg(missing_params: list[Param]) -> None:
    print(
        "Error, missing required "
        f"argument{'s' if len(missing_params) > 1 else ''}:"
    )
    for param in missing_params:
        help_line = f"\t--{param.help_name}\t({param.help_type})"
        if param.description:
            help_line += f" - {param.description}"
        print(help_line)


def params_to_kwargs(
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
        missing_params_msg(missing_params)
        exit()

    check_for_unexpected_args(params, kw_args)
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
    kwargs = params_to_kwargs(
        params=extract_code_params(code=func),
        docstring=format_docstring(func.__doc__ or ""),
    )
    func(**kwargs)


def code_to_ordered_params(code: Callable[..., Any]) -> OrderedDict:
    signature = inspect.signature(code)
    return OrderedDict(
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


def hints_from_ordered_params(ordered_params: OrderedDict) -> dict[str, type]:
    hints = {k: v.annotation for k, v in ordered_params.items()}.copy()
    # We don't care about the return value of the entrypoint
    if "return" in hints:
        hints.pop("return")
    return hints


def extract_code_params(code: Callable[..., Any]) -> list[Param]:
    tokens = tokenize_string(inspect.getsource(code))
    ordered_params = code_to_ordered_params(code)
    hints = hints_from_ordered_params(ordered_params)
    params: list[Param] = []
    prepended_comment = ""
    param = None

    while hints:
        token = next(tokens)
        if token.exact_type is COMMENT:
            prepended_comment = token.string
            continue
        # tokenize.NL -
        # when a logical line of code is continued over multiple lines
        if token.exact_type is NL:
            if not param:
                continue
            param.parse_line(prepended_comment)
        elif token.exact_type is NAME:
            if token.string not in hints:
                continue
            hints.pop(token.string)
            param = ordered_params[token.string]
            line_set = param.parse_line(token.line)
            if prepended_comment:
                param._set_description(prepended_comment)
            if not line_set:
                # Catch in the event a tokenize.NL is coming soon
                continue
        else:
            continue
        params.append(param)
        prepended_comment = ""
        param = None

    return params

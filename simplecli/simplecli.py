from __future__ import annotations
import contextlib
import inspect
import io
import os
import re
import sys
from collections import OrderedDict
from collections.abc import Generator
from tokenize import (
    COMMENT,
    NAME,
    NL,
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

try:
    from types import UnionType
except ImportError:  # pragma: no cover - coverage is generated via py3.12
    # Adapted from cpython/Lib/types.py which defines it as `int | str`.
    # This is ok because if UnionType is not imported, it is not supported.
    UnionType = Union[int, str]  # type: ignore


# 2023 - Clif Bratcher WIP


class Empty:
    pass


class DefaultIfBool:
    pass


_wrapped = False
ValueType = Union[type[DefaultIfBool], type[Empty], bool, float, int, str]
ArgDict = dict[str, ValueType]
ArgList = list[str]


class Param(inspect.Parameter):
    internal_only: bool  # Do not pass to wrapped function
    _required: bool  # Exit if a value is not present
    _optional: Union[bool, None] = None  # Mirrors `Optional` type

    def __init__(self, *argv: Any, **kwargs: Any) -> None:
        kwargs["annotation"] = kwargs.pop("annotation", Empty)
        kwargs["default"] = kwargs.pop("default", Empty)
        kwargs["kind"] = kwargs.pop(
            "kind", inspect.Parameter.POSITIONAL_OR_KEYWORD
        )
        # Allow 'name' as a positional parameter
        if "name" not in kwargs:
            if len(argv) == 0:
                raise TypeError("needs 'name' argument")
            kwargs["name"] = argv[0]
            argv = ()
        if kwargs["annotation"] not in get_args(ValueType):
            if get_origin(kwargs["annotation"]) not in (Union, UnionType):
                if kwargs["annotation"] is not Empty:
                    raise ValueError(
                        "annotation type "
                        f"'{type(kwargs['annotation']).__name__}' "
                        "is not currently supported!"
                    )
        param_description = str(kwargs.pop("description", ""))
        param_line = str(kwargs.pop("line", ""))
        param_value = kwargs.pop("value", Empty)
        param_internal_only = bool(kwargs.pop("internal_only", False))
        param_optional = kwargs.pop("optional", None)
        param_required = bool(kwargs.pop("required", True))
        super().__init__(*argv, **kwargs)
        self._value = param_value
        self.description = param_description
        self.internal_only = param_internal_only
        self._optional = (
            bool(param_optional) if param_optional is not None else None
        )
        self._required = param_required
        # Overrides required as these values are generally unused
        if not self.description:
            self.parse_or_prepend(param_line)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Param):
            return NotImplemented
        return (
            self.name == other.name
            and self.description == other.description
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
            f"required={self.required} "
            f"optional={self.optional} "
            f"value={value} "
        )

    @property
    def required(self) -> bool:
        # Internal only params never requires a value
        if self.internal_only:
            return False

        # Optional implies no required value
        if self.optional:
            return False

        # Existence of a default value implies no required value
        if self.default is not Empty:
            return False

        if bool in self.datatypes:
            return False

        # Fallback to set/default value
        return self._required

    @property
    def optional(self) -> bool:
        if self._optional is not None:
            return self._optional
        return len(self.datatypes) == 2 and type(None) in self.datatypes

    @property
    def help_name(self) -> str:
        return self.name.replace("_", "-")

    @property
    def help_type(self) -> str:
        if get_origin(self.annotation) in (Union, UnionType):
            typelist = ", ".join([a.__name__ for a in self.datatypes])
            return f"[{typelist}]"
        return self.annotation.__name__

    @property
    def value(self) -> ValueType:
        if self._value is not Empty:
            return self._value
        if self.default is not Empty:
            return self.default
        if bool in self.datatypes:
            return False
        return Empty

    def _set_description(self, line: str, force: bool = False) -> None:
        if self.description and not force:
            return
        self.description = re.sub(r"^#\s+", "", line.lstrip()).strip()

    def parse_or_prepend(
        self,
        line: str,
        comment: Union[None, str] = None,
        overwrite: bool = True,
    ) -> bool:
        # Necessary for < py3.12
        if not overwrite and self.description:
            return False

        line_set = False
        try:
            for token in tokenize_string(line):
                if token.exact_type is COMMENT:
                    self._set_description(token.string, force=True)
                    line_set = True
        except TokenError:
            line_set = False
        if comment:
            self._set_description(comment)
        return line_set

    @property
    def datatypes(self) -> list[type]:
        args = get_args(self.annotation)
        if args:
            return list(args)
        return [self.annotation]

    def validate(self, value: ValueType) -> bool:
        passed = False
        for expected_type in self.datatypes:
            if expected_type is type(None):
                continue
            try:
                expected_type(value)
                return True
            except ValueError:
                pass
        return passed

    def set_value(self, value: ValueType) -> None:
        result = value
        if self.validate(value) is False:
            raise ValueError(
                f"'{self.help_name}' must be of type {self.help_type}"
            )
        # Handle datatypes
        args = get_args(self.annotation)
        if args:
            for type_arg in args:
                with (
                    contextlib.suppress(TypeError),
                    contextlib.suppress(ValueError),
                ):
                    self._value = type_arg(value)
            return
        if value is DefaultIfBool:
            if bool not in self.datatypes:
                raise ValueError(f"'{self.help_name}' requires a value")
            result = self.default if self.default is not Empty else True
        elif bool in self.datatypes and self.default is Empty:
            result = value
        self._value = self.annotation(result)


def tokenize_string(string: str) -> Generator[TokenInfo, None, None]:
    return generate_tokens(io.StringIO(string).readline)


def help_text(
    filename: str,
    params: list[Param],
    docstring: str = "",
) -> str:
    help_msg = []
    if docstring:
        help_msg += ["Description:", docstring, ""]
    help_msg.append("Options:")
    positional = []
    max_attr_len = len(max(params, key=lambda x: len(x.help_name)).help_name)
    for param in params:
        if param.required:
            positional.append(param.help_name)
        help_line = f"  --{param.help_name}"
        offset = max_attr_len - len(param.help_name) + 2
        help_line += " " * offset
        if param.description:
            help_line += f" {param.description}"
        if param.default is not Empty:
            if type(param.default) in (int, float, str):
                help_line += f" (Default: {param.default})"
        help_msg.append(help_line)
    usage = f"  {filename} "
    if positional:
        usage += "[" + "] [".join(positional) + "]"
    return "\n".join(["Usage:", usage, ""] + help_msg)


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
    for key in kw_args:
        if key not in [a.name for a in params]:
            exit(f"Error: Unexpected argument '{key}'")


def missing_params_msg(missing_params: list[Param]) -> list[str]:
    mp_text = [
        (
            "Error, missing required "
            f"argument{'s' if len(missing_params) > 1 else ''}:"
        )
    ]
    for param in missing_params:
        mp_text.append(f"  --{param.help_name}")
        if param.description:
            mp_text[-1] += f"  {param.description}"
    return mp_text


def params_to_kwargs(
    params: list[Param],
    pos_args: ArgList,
    kw_args: ArgDict,
) -> ArgDict:
    missing_params = []
    try:
        for param in params:
            # Positional arguments take precedence
            if pos_args:
                param.set_value(pos_args.pop(0))
            elif param.name in kw_args:
                if kw_args[param.name] is DefaultIfBool:
                    # Invert the default value
                    param.set_value(
                        True if param.default is Empty else not param.default
                    )
                    continue
                param.set_value(kw_args[param.name])
                continue
            elif param.required:
                missing_params.append(param)
                continue
    except ValueError as e:
        exit(e.args[0])

    if pos_args:
        raise TypeError("Too many positional arguments!")

    if missing_params:
        raise TypeError(*missing_params_msg(missing_params))

    # If any value from kw_args is not in params, exit with prejiduce!
    check_for_unexpected_args(params, kw_args)
    return {param.name: param.value for param in params}


def format_docstring(docstring: str) -> str:
    if docstring.find("\t") != -1:
        raise ValueError(
            "For simplicity, tabs are not supported. Please remove tabs "
            "from your docstring to use pysimplecli. See also PEP 8: "
            "https://peps.python.org/pep-0008/#tabs-or-spaces"
        )

    start = end_offset = 0
    searching_for_start = True
    minimum_indent = 2
    lines = docstring.splitlines()
    for offset, line in enumerate(lines):
        indent = re.match(r"\s*", line).span()[1]  # type: ignore[union-attr]
        if indent != len(line):
            end_offset = 0  # Reset counter if we have a useful line
            minimum_indent = min(indent, minimum_indent)
            searching_for_start = False
        elif searching_for_start:
            start = offset + 1
        else:
            end_offset += 1

    aligned_lines = [line[minimum_indent:] for line in lines]
    return os.linesep.join(aligned_lines[start : len(lines) - end_offset])


def wrap(func: Callable[..., Any]) -> Callable[..., Any]:
    if func.__globals__["__name__"] != "__main__":
        return func
    global _wrapped
    if _wrapped:
        exit("Error, sorry only ONE `@wrap` decorator allowed!")
    _wrapped = True
    filename = sys.argv[0]
    argv = sys.argv[1:]
    params = extract_code_params(code=func)
    pos_args, kw_args = clean_args(argv)
    params.append(
        Param("help", description="Show this message", internal_only=True)
    )
    version = func.__globals__.get("__version__", "")
    if version:
        params.append(
            Param(
                "version",
                description=f"Display {filename} version",
                internal_only=True,
            )
        )

    if "help" in kw_args:
        exit(help_text(filename, params, format_docstring(func.__doc__ or "")))

    if "version" in kw_args:
        if version != "":
            exit(f"{filename} version {version}")

    # Strip internal-only
    params = [param for param in params if not param.internal_only]
    try:
        kwargs = params_to_kwargs(params, pos_args, kw_args)
    except TypeError as e:
        exit("\n".join(e.args))

    return func(**kwargs)


def code_to_ordered_params(code: Callable[..., Any]) -> OrderedDict:
    signature = inspect.signature(code)
    empty = inspect._empty
    return OrderedDict(
        (
            k,
            Param(
                name=v.name,
                default=Empty if v.default is empty else v.default,
                annotation=Empty if v.annotation is empty else v.annotation,
                kind=v.kind,
            ),
        )
        for k, v in signature.parameters.items()
    )


def process_comment(
    param: Param | None,
    params: list[Param],
    token: TokenInfo,
) -> str:
    comment = token.string
    if params and param is None:
        params[-1].parse_or_prepend(token.line, comment)
        comment = ""
    elif param:
        param.parse_or_prepend(token.line, comment, False)
    return comment


def extract_code_params(code: Callable[..., Any]) -> list[Param]:
    ordered_params = code_to_ordered_params(code)
    hints = {k: v.annotation for k, v in ordered_params.items()}.copy()
    comment = ""
    param = None
    params: list[Param] = []

    for token in tokenize_string(inspect.getsource(code)):
        if token.exact_type is COMMENT:
            comment = process_comment(param, params, token)
            continue
        # tokenize.NL -
        # when a logical line of code is continued over multiple lines
        if token.exact_type is NL and param:
            param.parse_or_prepend(token.line, comment)
        elif token.exact_type is NAME and token.string in hints:
            if param is not None:
                comment = ""
                params.append(param)
                param = None
            hints.pop(token.string)
            param = ordered_params.pop(token.string)
            if not param.parse_or_prepend(token.line, comment):
                # Catch in the event a tokenize.NL is coming soon
                continue
        else:
            continue
        comment = ""
        params.append(param)
        param = None
    if param:
        params.append(param)
    return params

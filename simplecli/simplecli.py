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


class Empty:
    pass


_wrapped = False
# Overloaded placeholder for a potential boolean
DefaultIfBool = "Crazy going slowly am I, 6, 5, 4, 3, 2, 1, switch!"
ValueType = Union[type[Empty], bool, float, int, str]
ArgDict = dict[str, ValueType]
ArgList = list[str]


class Param(inspect.Parameter):
    internal_only: bool  # Do not pass to wrapped function
    optional: bool  # Value can be `None`, mirrors `Optional` type
    required: bool  # Exit if a value is not present

    def __init__(self, *argv: Any, **kwargs: Any) -> None:
        if "kind" not in kwargs:
            kwargs["kind"] = inspect.Parameter.POSITIONAL_OR_KEYWORD
        for required_arg in ("annotation", "name"):
            if required_arg not in kwargs:
                raise TypeError(
                    f"needs keyword-only argument '{required_arg}'"
                )
        if kwargs["annotation"] not in get_args(ValueType):
            if get_origin(kwargs["annotation"]) is not Union:
                if kwargs["annotation"] is not Empty:
                    raise ValueError(
                        "annotation type "
                        f"'{type(kwargs['annotation']).__name__}' "
                        "is not currently supported!"
                    )
        kwargs["annotation"] = kwargs.pop("annotation", Empty)
        kwargs["default"] = kwargs.pop("default", Empty)
        param_description = str(kwargs.pop("description", ""))
        param_line = str(kwargs.pop("line", ""))
        param_value = kwargs.pop("value", Empty)
        param_internal_only = bool(kwargs.pop("internal_only", False))
        param_optional = bool(kwargs.pop("optional", False))
        param_required = bool(kwargs.pop("required", True))
        super().__init__(*argv, **kwargs)
        self._value = param_value
        self.description = param_description
        self.internal_only = param_internal_only
        self.optional = param_optional
        self.required = param_required
        # Overrides required as these values are generally unused
        if self.internal_only:
            self.required = False
        if not self.description:
            self.parse_line(param_line)

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
    def help_name(self) -> str:
        return self.name.replace("_", "-")

    @property
    def help_type(self) -> str:
        if get_origin(self.annotation) is Union:
            typelist = ", ".join([a.__name__ for a in self.datatypes])
            return f"[{typelist}]"
        return self.annotation.__name__

    @property
    def value(self) -> ValueType:
        if self._value is not Empty:
            return self._value
        if self.default is not Empty:
            return self.default
        return Empty

    def _set_description(self, line: str, force: bool = False) -> None:
        if self.description and not force:
            return
        self.description = re.sub(r"^#\s+", "", line.lstrip()).strip()

    def parse_or_prepend(
        self,
        line: str,
        comment: str,
        overwrite: bool = True,
    ) -> bool:
        if not overwrite and self.description:
            return False

        line_set = self.parse_line(line)
        if comment:
            self._set_description(comment)
        return line_set

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
                self._set_description(token.string, force=True)
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
        return [self.annotation]

    def validate(self, value: ValueType) -> bool:
        passed = False
        for expected_type in self.datatypes:
            try:
                expected_type(value)
                return True
            except ValueError:
                pass
        return passed

    def set_value(self, value: ValueType) -> None:
        if self.validate(value) is False:
            raise ValueError(
                f"'{self.help_name}' must be of type {self.help_type}"
            )
        # Handle datatypes
        args = get_args(self.annotation)
        if args:
            for type_arg in args:
                with contextlib.suppress(TypeError):
                    self._value = type_arg(value)
            return
        if value is DefaultIfBool:
            if self.annotation is not bool:
                raise ValueError(f"'{self.help_name}' requires a value")
            if self.default != Empty:
                self._value = self.annotation(self.default)
                return
            else:
                self._value = self.annotation(True)
                return
        self._value = self.annotation(value)


def tokenize_string(string: str) -> Generator[TokenInfo, None, None]:
    return generate_tokens(io.StringIO(string).readline)


def help_text(
    filename: str,
    params: list[Param],
    docstring: str = "",
) -> str:
    help_msg = ["Usage: ", f"\t{filename} ..."]
    if docstring:
        help_msg += ["Description: ", f"{docstring}"]
    help_msg.append("Options:")
    for param in params:
        if get_origin(param.annotation) is Union:
            types = [a.__name__ for a in get_args(param.annotation)]
            if "NoneType" in types:
                types.remove("NoneType")
                arg_types = " ".join(types)
                arg_types += " OPTIONAL"
            else:
                arg_types = param.help_type
                arg_types += " OPTIONAL"
        else:
            arg_types = param.help_type
        help_line = f" --{param.help_name}"
        if arg_types != "_empty":
            help_line += f"\t\t({arg_types})\t"
        if param.default is not Empty:
            help_line += f" [Default: {param.default}]"
        help_line += f" {param.description}"
        help_msg.append(help_line)
    return "\n".join(help_msg)


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
        mp_text.append(f"\t--{param.help_name}\t({param.help_type})")
        if param.description:
            mp_text[-1] += f" - {param.description}"
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
        exit("Error, sorry only ONE `@wrap` decorator allowed!")
    _wrapped = True
    filename = sys.argv[0]
    argv = sys.argv[1:]
    params = extract_code_params(code=func)
    pos_args, kw_args = clean_args(argv)
    version = func.__globals__.get("__version__", "")
    if version:
        params.append(
            Param(name="version", annotation=Empty, internal_only=True)
        )
    params.append(Param(name="help", annotation=Empty, internal_only=True))
    if "help" in kw_args:
        exit(help_text(filename, params, format_docstring(func.__doc__ or "")))

    if "version" in kw_args:
        if version != "":
            exit(f"Version: {version}")

    # Strip internal-only
    params = [param for param in params if not param.internal_only]

    try:
        kwargs = params_to_kwargs(
            params=params,
            pos_args=pos_args,
            kw_args=kw_args,
        )
    except TypeError as e:
        exit("\n".join(e.args))
    func(**kwargs)


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
    comment = ""
    param = None
    params: list[Param] = []

    depth = 0
    for token in tokens:
        depth += 1
        if token.exact_type is COMMENT:
            comment = token.string
            if params and param is None:
                params[-1].parse_or_prepend(token.line, comment)
                comment = ""
            elif param:
                param.parse_or_prepend(token.line, comment, False)
            continue
        # tokenize.NL -
        # when a logical line of code is continued over multiple lines
        if token.exact_type is NL and param:
            param.parse_or_prepend(token.line, comment)
        elif token.exact_type is NAME and token.string in hints:
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

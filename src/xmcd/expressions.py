"""Composable, immutable Mathcad expressions; operators build syntax, never evaluate."""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from numbers import Real

from lxml import etree as ET

ML = "http://schemas.mathsoft.com/math30"


def node(tag, *children, text=None, **attrs):
    result = ET.Element(f"{{{ML}}}{tag}", {k: str(v) for k, v in attrs.items()})
    result.text = text
    result.extend(c.to_xml() if isinstance(c, Expr) else c for c in children)
    return result


class Expr:
    def to_xml(self) -> ET._Element:
        raise NotImplementedError

    def __bool__(self):
        raise TypeError("Mathcad expressions have no Python truth value; use explicit comparisons")

    def __add__(self, other):
        return Operator("plus", self, other)

    def __radd__(self, other):
        return Operator("plus", other, self)

    def __sub__(self, other):
        return Operator("minus", self, other)

    def __rsub__(self, other):
        return Operator("minus", other, self)

    def __mul__(self, other):
        return Operator("mult", self, other)

    def __rmul__(self, other):
        return Operator("mult", other, self)

    def __truediv__(self, other):
        return Operator("div", self, other)

    def __rtruediv__(self, other):
        return Operator("div", other, self)

    def __pow__(self, other):
        return Operator("pow", self, other)

    def __rpow__(self, other):
        return Operator("pow", other, self)

    def __neg__(self):
        return Operator("neg", self)

    def __abs__(self):
        return Operator("absval", self)

    def __lt__(self, other):
        return Operator("lessThan", self, other)

    def __le__(self, other):
        return Operator("lessOrEqual", self, other)

    def __gt__(self, other):
        return Operator("greaterThan", self, other)

    def __ge__(self, other):
        return Operator("greaterOrEqual", self, other)

    def eq(self, other):
        return Operator("equal", self, other)

    def ne(self, other):
        return Operator("notEqual", self, other)

    def __and__(self, other):
        return Operator("and", self, other)

    def __or__(self, other):
        return Operator("or", self, other)

    def __invert__(self):
        return Operator("not", self)

    def __getitem__(self, index):
        if isinstance(index, tuple):
            if len(index) != 2:
                raise ValueError("Matrix indexing requires (row, column)")
            index = Sequence(*index)
        return Operator("indexer", self, index)

    def column(self, index):
        return Operator("matcol", self, index)

    def row(self, index):
        return Operator("matrow", self, index)

    def vectorize(self):
        return Operator("vectorize", self)

    def determinant(self):
        return Operator("determinant", self)

    def conjugate(self):
        return Operator("conjugate", self)

    def __call__(self, *arguments):
        return Call(self, *arguments)

    @property
    def T(self):
        return Operator("transpose", self)


def expr(value) -> Expr:
    if isinstance(value, Expr):
        return value
    if isinstance(value, str):
        return Symbol(value)
    if isinstance(value, (Real, Decimal)):
        return Number(value)
    if isinstance(value, complex):
        return Number(value.real) + Operator("mult", Number(value.imag), Imaginary(1))
    raise TypeError(f"Cannot convert {type(value).__name__} to a Mathcad expression")


@dataclass(frozen=True, eq=False)
class Number(Expr):
    value: Real | Decimal

    def __post_init__(self):
        if not isinstance(self.value, (Real, Decimal)) or not math.isfinite(self.value):
            raise ValueError("Number requires a finite real value")

    def to_xml(self):
        return node(
            "real", text=str(int(self.value)) if isinstance(self.value, bool) else str(self.value)
        )


@dataclass(frozen=True, eq=False)
class Imaginary(Number):
    def to_xml(self):
        return node("imag", text=str(self.value))


@dataclass(frozen=True, eq=False)
class Symbol(Expr):
    name: str
    subscript: str | None = None

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Symbol name must be a nonempty string")

    def to_xml(self):
        attrs = {"{http://www.w3.org/XML/1998/namespace}space": "preserve"}
        if self.subscript is not None:
            attrs["subscript"] = self.subscript
        return node("id", text=self.name, **attrs)


@dataclass(frozen=True, eq=False)
class String(Expr):
    value: str

    def to_xml(self):
        return node(
            "str", text=self.value, **{"{http://www.w3.org/XML/1998/namespace}space": "preserve"}
        )


@dataclass(frozen=True, eq=False)
class Placeholder(Expr):
    def to_xml(self):
        return node("placeholder")


UNARY = frozenset(
    [
        "absval",
        "conjugate",
        "factorial",
        "neg",
        "not",
        "sqrt",
        "transpose",
        "vectorize",
        "vectorSum",
        "determinant",
    ]
)
BINARY = frozenset(
    [
        "and",
        "crossProduct",
        "div",
        "equal",
        "greaterOrEqual",
        "greaterThan",
        "indexer",
        "lessOrEqual",
        "lessThan",
        "log",
        "matrow",
        "matcol",
        "minus",
        "mult",
        "notEqual",
        "nthRoot",
        "or",
        "plus",
        "pow",
        "xor",
    ]
)


@dataclass(frozen=True, eq=False, init=False)
class Operator(Expr):
    name: str
    arguments: tuple[Expr, ...]

    def __init__(self, name, *arguments):
        count = 1 if name in UNARY else 2 if name in BINARY else None
        if count is None or len(arguments) != count:
            raise ValueError(f"Unknown operator or wrong arity: {name} ({len(arguments)})")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "arguments", tuple(expr(a) for a in arguments))

    def to_xml(self):
        return node("apply", node(self.name), *self.arguments)


@dataclass(frozen=True, eq=False, init=False)
class Sequence(Expr):
    values: tuple[Expr, ...]

    def __init__(self, *values):
        if len(values) < 2:
            raise ValueError("A sequence requires at least two values")
        object.__setattr__(self, "values", tuple(expr(a) for a in values))

    def to_xml(self):
        return node("sequence", *self.values)


@dataclass(frozen=True, eq=False, init=False)
class Call(Expr):
    function: Expr
    arguments: tuple[Expr, ...]

    def __init__(self, function, *arguments):
        if not arguments:
            raise ValueError("Mathcad calls require at least one argument")
        object.__setattr__(self, "function", expr(function))
        object.__setattr__(self, "arguments", tuple(expr(a) for a in arguments))

    def to_xml(self):
        argument = self.arguments[0] if len(self.arguments) == 1 else Sequence(*self.arguments)
        return node("apply", self.function, argument)


class Functions:
    """Open function namespace: f.sin(x), f.lsolve(A, b), f['custom-name'](x)."""

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return Symbol(name)

    def __getitem__(self, name):
        return Symbol(name)


f = Functions()


@dataclass(frozen=True, eq=False)
class Given(Expr):
    """Start a solve block. Place guesses before it and constraints after it."""

    def to_xml(self):
        return Symbol("Given").to_xml()


@dataclass(frozen=True, eq=False)
class Solver(Expr):
    """Native solve terminator, called like Solver('Find')(x, y).

    Keep this distinct from an ordinary function named Find: Mathcad stores
    solver options on a dedicated operator in the expression tree.
    """

    name: str = "Find"
    method: str | None = None

    def __post_init__(self):
        if self.name not in {"Find", "Minerr", "Minimize", "Maximize", "Odesolve"}:
            raise ValueError("Unknown solve terminator")
        methods = (
            {"fixed", "adaptive", "radau", "adams/bdf (auto)"}
            if self.name == "Odesolve"
            else {"linear", "conjugate", "newton", "quadratic", "levenberg"}
        )
        if self.method is not None and self.method not in methods:
            raise ValueError(f"Unsupported method for {self.name}: {self.method}")

    def to_xml(self):
        attrs = {}
        if self.method is not None:
            attrs["method"] = self.method
            if self.name != "Odesolve":
                attrs["auto-method"] = "false"
        return node(self.name, **attrs)


@dataclass(frozen=True, eq=False, init=False)
class Matrix(Expr):
    rows: tuple[tuple[Expr, ...], ...]

    def __init__(self, rows):
        rows = tuple(tuple(expr(a) for a in row) for row in rows)
        if not rows or not rows[0] or any(len(r) != len(rows[0]) for r in rows):
            raise ValueError("Matrix must be nonempty and rectangular")
        object.__setattr__(self, "rows", rows)

    @classmethod
    def vector(cls, values):
        return cls([[v] for v in values])

    def to_xml(self):
        return node(
            "matrix",
            *(v for col in zip(*self.rows) for v in col),
            rows=len(self.rows),
            cols=len(self.rows[0]),
        )


@dataclass(frozen=True, eq=False)
class Range(Expr):
    start: object
    stop: object
    second: object | None = None

    def to_xml(self):
        start = expr(self.start) if self.second is None else Sequence(self.start, self.second)
        return node("range", start, expr(self.stop))


@dataclass(frozen=True, eq=False)
class Function(Expr):
    name: object
    parameters: tuple

    def __post_init__(self):
        if not self.parameters:
            raise ValueError("Function needs parameters")
        object.__setattr__(self, "parameters", tuple(expr(v) for v in self.parameters))
        if any(not isinstance(v, Symbol) for v in self.parameters):
            raise TypeError("Function parameters must be symbols")

    def to_xml(self):
        return node("function", expr(self.name), node("boundVars", *self.parameters))

    def __call__(self, *arguments):
        return Call(self.name, *arguments)


@dataclass(frozen=True, eq=False)
class Define(Expr):
    lhs: object
    rhs: object
    kind: str = "normal"

    def to_xml(self):
        kinds = {"normal": "define", "local": "localDefine", "global": "globalDefine"}
        if self.kind not in kinds:
            raise ValueError("Definition kind must be normal, local or global")
        return node(kinds[self.kind], expr(self.lhs), expr(self.rhs))


@dataclass(frozen=True, eq=False)
class Evaluate(Expr):
    expression: object
    unit: object | None = None

    def to_xml(self):
        result = node("eval", expr(self.expression))
        result.append(node("unitOverride", Placeholder() if self.unit is None else expr(self.unit)))
        return result


@dataclass(frozen=True, eq=False)
class Symbolic(Expr):
    expression: object
    commands: tuple = ()

    def to_xml(self):
        result = node("symEval", expr(self.expression))
        for command in self.commands:
            result.append(
                node("command", Sequence(*command) if isinstance(command, tuple) else expr(command))
            )
        return result


@dataclass(frozen=True, eq=False)
class Derivative(Expr):
    expression: object
    variable: object
    degree: object = 1

    def to_xml(self):
        return node(
            "apply",
            node("derivative"),
            node("lambda", node("boundVars", expr(self.variable)), expr(self.expression)),
            node("degree", expr(self.degree)),
        )


@dataclass(frozen=True, eq=False)
class Integral(Expr):
    expression: object
    variable: object
    lower: object | None = None
    upper: object | None = None
    _operator = "integral"

    def to_xml(self):
        if (self.lower is None) != (self.upper is None):
            raise ValueError("Specify both bounds or neither")
        result = node(
            "apply",
            node(self._operator),
            node("lambda", node("boundVars", expr(self.variable)), expr(self.expression)),
        )
        if self.lower is not None:
            result.append(node("bounds", expr(self.lower), expr(self.upper)))
        return result


class Sum(Integral):
    _operator = "summation"


class Product(Integral):
    _operator = "product"


@dataclass(frozen=True, eq=False, init=False)
class Program(Expr):
    statements: tuple[Expr, ...]

    def __init__(self, *statements):
        if len(statements) < 2:
            raise ValueError("Native programs require at least two statements")
        object.__setattr__(self, "statements", tuple(expr(s) for s in statements))

    def to_xml(self):
        return node("program", *self.statements)


@dataclass(frozen=True, eq=False)
class If(Expr):
    condition: object
    value: object

    def to_xml(self):
        return node("ifThen", expr(self.condition), expr(self.value))


@dataclass(frozen=True, eq=False)
class Otherwise(Expr):
    value: object

    def to_xml(self):
        return node("otherwise", expr(self.value))


@dataclass(frozen=True, eq=False)
class For(Expr):
    variable: object
    values: object
    body: object

    def to_xml(self):
        return node("for", expr(self.variable), expr(self.values), expr(self.body))


@dataclass(frozen=True, eq=False)
class While(Expr):
    condition: object
    body: object

    def to_xml(self):
        return node("while", expr(self.condition), expr(self.body))


@dataclass(frozen=True, eq=False)
class Return(Expr):
    value: object

    def to_xml(self):
        return node("return", expr(self.value))


@dataclass(frozen=True, eq=False)
class Break(Expr):
    def to_xml(self):
        return node("break")


@dataclass(frozen=True, eq=False)
class Continue(Expr):
    def to_xml(self):
        return node("continue")


@dataclass(frozen=True, eq=False)
class TryCatch(Expr):
    expression: object
    fallback: object

    def to_xml(self):
        return node("tryCatch", expr(self.expression), expr(self.fallback))

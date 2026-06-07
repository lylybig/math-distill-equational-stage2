from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class EquationSyntaxError(ValueError):
    """Raised when an equation string cannot be parsed."""


@dataclass(frozen=True)
class Expr:
    kind: str
    value: str | None = None
    left: "Expr | None" = None
    right: "Expr | None" = None

    @staticmethod
    def var(name: str) -> "Expr":
        return Expr("var", value=name)

    @staticmethod
    def mul(left: "Expr", right: "Expr") -> "Expr":
        return Expr("mul", left=left, right=right)

    def to_tuple(self) -> tuple:
        if self.kind == "var":
            return ("var", self.value)
        if self.kind == "mul":
            assert self.left is not None
            assert self.right is not None
            return ("mul", self.left.to_tuple(), self.right.to_tuple())
        raise ValueError(f"unknown expression kind: {self.kind}")

    def variable_names(self) -> Iterable[str]:
        if self.kind == "var":
            assert self.value is not None
            yield self.value
            return
        assert self.left is not None
        assert self.right is not None
        yield from self.left.variable_names()
        yield from self.right.variable_names()


@dataclass(frozen=True)
class Equation:
    left: Expr
    right: Expr

    def variables(self) -> list[str]:
        seen: set[str] = set()
        names: list[str] = []
        for name in list(self.left.variable_names()) + list(self.right.variable_names()):
            if name not in seen:
                seen.add(name)
                names.append(name)
        return names


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    position: int


def parse_equation(source: str) -> Equation:
    parser = _Parser(_tokenize(source))
    equation = parser.parse_equation()
    parser.expect_end()
    return equation


def canonical_equation_signature(source: str) -> str:
    equation = parse_equation(source)
    names: dict[str, str] = {}

    def encode(expr: Expr) -> str:
        if expr.kind == "var":
            assert expr.value is not None
            if expr.value not in names:
                names[expr.value] = f"v{len(names)}"
            return names[expr.value]
        assert expr.left is not None
        assert expr.right is not None
        return f"({encode(expr.left)}*{encode(expr.right)})"

    return f"{encode(equation.left)}={encode(equation.right)}"


def _tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    while i < len(source):
        char = source[i]
        if char.isspace():
            i += 1
            continue
        if char in "()*=":
            tokens.append(Token(char, char, i))
            i += 1
            continue
        if char.isalpha() or char == "_":
            start = i
            i += 1
            while i < len(source) and (source[i].isalnum() or source[i] == "_"):
                i += 1
            tokens.append(Token("ident", source[start:i], start))
            continue
        raise EquationSyntaxError(f"unexpected character {char!r} at position {i}")
    return tokens


class _Parser:
    def __init__(self, tokens: list[Token]):
        self._tokens = tokens
        self._index = 0

    def parse_equation(self) -> Equation:
        left = self.parse_expr()
        self._expect("=")
        right = self.parse_expr()
        return Equation(left=left, right=right)

    def parse_expr(self) -> Expr:
        expr = self.parse_atom()
        while self._match("*"):
            expr = Expr.mul(expr, self.parse_atom())
        return expr

    def parse_atom(self) -> Expr:
        token = self._peek()
        if token is None:
            raise EquationSyntaxError("expected expression, got end of input")
        if token.kind == "ident":
            self._index += 1
            return Expr.var(token.value)
        if self._match("("):
            expr = self.parse_expr()
            self._expect(")")
            return expr
        raise EquationSyntaxError(f"expected expression at position {token.position}")

    def expect_end(self) -> None:
        token = self._peek()
        if token is not None:
            raise EquationSyntaxError(f"unexpected token {token.value!r} at position {token.position}")

    def _peek(self) -> Token | None:
        if self._index >= len(self._tokens):
            return None
        return self._tokens[self._index]

    def _match(self, kind: str) -> bool:
        token = self._peek()
        if token is None or token.kind != kind:
            return False
        self._index += 1
        return True

    def _expect(self, kind: str) -> Token:
        token = self._peek()
        if token is None:
            raise EquationSyntaxError(f"expected {kind!r}, got end of input")
        if token.kind != kind:
            raise EquationSyntaxError(f"expected {kind!r} at position {token.position}")
        self._index += 1
        return token

# Copyright 2026 KiraFlux
# SPDX-License-Identifier: Apache-2.0

"""
Token
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, ClassVar, Final, Mapping, Optional

from miz._operators import BinaryOp, UnaryOp


@dataclass
class SourcePosition:
    """Source code position"""
    name: str
    cursor: int
    line: int
    col: int

    def clone(self) -> SourcePosition:
        return SourcePosition(self.name, self.cursor, self.line, self.col)

    def advance(self, chars: int) -> None:
        self.cursor += chars
        self.col += chars

    def new_line(self) -> None:
        self.line += 1
        self.col = 1

    def __str__(self):
        return f"'{self.name}' {self.line}:{self.col}"


class Token[T]:
    """Token with value"""

    __dummy: ClassVar = None

    @classmethod
    def dummy(cls):
        """Create Dummy token"""
        if cls.__dummy is None:
            cls.__dummy = cls(
                token_type=TokenType.identifier,
                value=None,
                source_position=SourcePosition("", 0, 1, 1)
            )

        return cls.__dummy

    def __init__(self, *, token_type: TokenType, value: T, source_position: SourcePosition) -> None:
        self.type = token_type
        self.value: Final = value
        self.source_position: Final = source_position

    def __str__(self) -> str:
        if self.value is None:
            return f"{self.type.name}"
        return f"{self.type.name}({repr(self.value)}) at {self.source_position}"


class TokenType(Enum):
    """Token types with regex patterns"""

    _ignore_ = ["_p"]

    @staticmethod
    def _word(lexeme: str) -> tuple[str, Token[None], None]:
        return (
            lexeme,
            Token[None],
            None
        )

    # Logical operators
    logical_not = _word(r'not\b')
    logical_and = _word(r'and\b')
    logical_or = _word(r'or\b')
    type_cast = _word(r'as\b')

    # Keywords
    keyword_pub = _word(r'pub\b')
    keyword_var = _word(r'var\b')
    keyword_def = _word(r'def\b')
    keyword_fn = _word(r'fn\b')
    keyword_sig = _word(r'sig\b')
    keyword_struct = _word(r'struct\b')
    keyword_if = _word(r'if\b')
    keyword_else = _word(r'else\b')
    keyword_loop = _word(r'loop\b')
    keyword_return = _word(r'return\b')
    keyword_break = _word(r'break\b')
    keyword_continue = _word(r'continue\b')
    keyword_undefined = _word(r'undefined\b')

    # Identifiers
    identifier = (r'[a-zA-Z_][a-zA-Z0-9_]*', Token[str], str)
    comment = (r'//.*', Token[str], str)

    # Literals
    string = (r'\"(?:[^\"\\]|\\.)*\"', Token[str], lambda s: s[1:-1])
    scientific_real = (r'-?\d+(?:\.\d+)?[eE][-+]?\d+', Token[float], float)
    real = (r'-?\d+\.\d+', Token[float], float)
    hex_integer = (r'0x[0-9a-fA-F]+', Token[int], lambda s: int(s, 16))
    binary_integer = (r'0b[01]+', Token[int], lambda s: int(s[2:], 2))
    integer = (r'-?\d+', Token[int], int)
    char = (r'\'(?:[^\'\\]|\\.)\'', Token[int], lambda s: ord(s[1:-1]))

    # Brackets
    paren_open = _word(r'\(')
    paren_close = _word(r'\)')
    bracket_open = _word(r'\[')
    bracket_close = _word(r'\]')
    brace_open = _word(r'\{')
    brace_close = _word(r'\}')

    # Operators
    shift_left = _word(r'<<')
    shift_right = _word(r'>>')
    equal = _word(r'==')
    not_equal = _word(r'!=')
    less_equal = _word(r'<=')
    greater_equal = _word(r'>=')

    # Single character operators
    plus = _word(r'\+')
    minus = _word(r'-')
    star = _word(r'\*')
    slash = _word(r'/')
    percent = _word(r'%')
    ampersand = _word(r'&')
    pipe = _word(r'\|')
    caret = _word(r'\^')
    less = _word(r'<')
    greater = _word(r'>')

    # Delimiters
    comma = _word(r',')
    colon = _word(r':')
    dot = _word(r'\.')
    assign = _word(r'=')

    # Whitespace
    whitespace = _word(r'[ \t]+')
    newline = _word(r'\n')

    def __init__(self, regex: str, token_class: type[Token], value_from_lexeme: Optional[Callable[[str], Any]]) -> None:
        self.pattern: Final[re.Pattern[str]] = re.compile(regex)
        self._token_class: Final[type[Token]] = token_class
        self._value_from_lexeme: Final = value_from_lexeme

    def make(self, lexeme: str, source_position: SourcePosition) -> Token:
        """Create token from lexeme"""
        return self._token_class(
            token_type=self,
            value=None if self._value_from_lexeme is None else self._value_from_lexeme(lexeme),
            source_position=source_position,
        )

    def skip(self) -> bool:
        """Should this token be skipped in token stream?"""
        return self in {TokenType.comment, TokenType.whitespace}

    @classmethod
    def integer_types(cls) -> set[TokenType]:
        """All integer literal types"""
        return {cls.integer, cls.hex_integer, cls.binary_integer, cls.char}

    @classmethod
    def real_types(cls) -> set[TokenType]:
        """All real literal types"""
        return {cls.real, cls.scientific_real}

    @classmethod
    def build_precedence(cls) -> Mapping[TokenType, int]:
        """Build operator precedence table"""
        return {
            # Logical (lowest)
            cls.logical_or: 1,
            cls.logical_and: 2,

            # Comparison
            cls.equal: 3,
            cls.not_equal: 3,
            cls.less: 3,
            cls.greater: 3,
            cls.less_equal: 3,
            cls.greater_equal: 3,

            # Bitwise
            cls.pipe: 4,
            cls.caret: 5,
            cls.ampersand: 6,
            cls.shift_left: 7,
            cls.shift_right: 7,

            # Additive
            cls.plus: 8,
            cls.minus: 8,

            # Multiplicative
            cls.star: 9,
            cls.slash: 9,
            cls.percent: 9,

            # Postfix
            cls.dot: 10,
            cls.bracket_open: 10,
            cls.paren_open: 10,

            # type cast
            cls.type_cast: 11,
        }

    @classmethod
    def build_unary_operator_map(cls) -> Mapping[TokenType, UnaryOp]:
        """Build token to unary operator table"""
        return {
            cls.plus: UnaryOp.positive,
            cls.minus: UnaryOp.negative,
            cls.star: UnaryOp.star,
            cls.ampersand: UnaryOp.address_of,
            cls.logical_not: UnaryOp.logical_not,
        }

    @classmethod
    def build_binary_operator_map(cls) -> Mapping[TokenType, BinaryOp]:
        """Build token to unary operator table"""
        return {
            cls.plus: BinaryOp.add,
            cls.minus: BinaryOp.sub,
            cls.star: BinaryOp.mul,
            cls.slash: BinaryOp.div,
            cls.percent: BinaryOp.mod,
            cls.ampersand: BinaryOp.bitwise_and,
            cls.pipe: BinaryOp.bitwise_or,
            cls.caret: BinaryOp.bitwise_xor,
            cls.shift_left: BinaryOp.shift_left,
            cls.shift_right: BinaryOp.shift_right,
            cls.equal: BinaryOp.equal,
            cls.not_equal: BinaryOp.not_equal,
            cls.less: BinaryOp.less,
            cls.greater: BinaryOp.greater,
            cls.less_equal: BinaryOp.less_equal,
            cls.greater_equal: BinaryOp.greater_equal,
            cls.logical_and: BinaryOp.logical_and,
            cls.logical_or: BinaryOp.logical_or,
            cls.type_cast: BinaryOp.type_cast,
        }

    @classmethod
    def build_precedence(cls) -> Mapping[TokenType, int]:
        """Build operator precedence table"""
        return {
            # Logical (lowest)
            cls.logical_or: 1,
            cls.logical_and: 2,

            # Comparison
            cls.equal: 3,
            cls.not_equal: 3,
            cls.less: 3,
            cls.greater: 3,
            cls.less_equal: 3,
            cls.greater_equal: 3,

            # Bitwise
            cls.pipe: 4,
            cls.caret: 5,
            cls.ampersand: 6,
            cls.shift_left: 7,
            cls.shift_right: 7,

            # Additive
            cls.plus: 8,
            cls.minus: 8,

            # Multiplicative
            cls.star: 9,
            cls.slash: 9,
            cls.percent: 9,

            # Postfix
            cls.dot: 10,
            cls.bracket_open: 10,
            cls.paren_open: 10,

            # type cast
            cls.type_cast: 11,
        }

    @classmethod
    def build_unary_operator_map(cls) -> Mapping[TokenType, UnaryOp]:
        """Build token to unary operator table"""
        return {
            cls.plus: UnaryOp.positive,
            cls.minus: UnaryOp.negative,
            cls.star: UnaryOp.star,
            cls.ampersand: UnaryOp.address_of,
            cls.logical_not: UnaryOp.logical_not,
        }

    @classmethod
    def build_binary_operator_map(cls) -> Mapping[TokenType, BinaryOp]:
        """Build token to unary operator table"""
        return {
            cls.plus: BinaryOp.add,
            cls.minus: BinaryOp.sub,
            cls.star: BinaryOp.mul,
            cls.slash: BinaryOp.div,
            cls.percent: BinaryOp.mod,
            cls.ampersand: BinaryOp.bitwise_and,
            cls.pipe: BinaryOp.bitwise_or,
            cls.caret: BinaryOp.bitwise_xor,
            cls.shift_left: BinaryOp.shift_left,
            cls.shift_right: BinaryOp.shift_right,
            cls.equal: BinaryOp.equal,
            cls.not_equal: BinaryOp.not_equal,
            cls.less: BinaryOp.less,
            cls.greater: BinaryOp.greater,
            cls.less_equal: BinaryOp.less_equal,
            cls.greater_equal: BinaryOp.greater_equal,
            cls.logical_and: BinaryOp.logical_and,
            cls.logical_or: BinaryOp.logical_or,
            cls.type_cast: BinaryOp.type_cast,
        }

# Copyright 2026 KiraFlux
# SPDX-License-Identifier: Apache-2.0

"""
Token
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import Callable
from typing import Final
from typing import Optional


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

    # Logical operators
    logical_not = (r'not\b', Token[None], None)
    logical_and = (r'and\b', Token[None], None)
    logical_or = (r'or\b', Token[None], None)
    type_cast = (r'as\b', Token[None], None)

    # Keywords
    keyword_pub = (r'pub\b', Token[None], None)
    keyword_var = (r'var\b', Token[None], None)
    keyword_def = (r'def\b', Token[None], None)
    keyword_fn = (r'fn\b', Token[None], None)
    keyword_sig = (r'sig\b', Token[None], None)
    keyword_struct = (r'struct\b', Token[None], None)
    keyword_if = (r'if\b', Token[None], None)
    keyword_else = (r'else\b', Token[None], None)
    keyword_loop = (r'loop\b', Token[None], None)
    keyword_return = (r'return\b', Token[None], None)
    keyword_break = (r'break\b', Token[None], None)
    keyword_continue = (r'continue\b', Token[None], None)
    keyword_undefined = (r'undefined\b', Token[None], None)

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
    paren_open = (r'\(', Token[None], None)
    paren_close = (r'\)', Token[None], None)
    bracket_open = (r'\[', Token[None], None)
    bracket_close = (r'\]', Token[None], None)
    brace_open = (r'\{', Token[None], None)
    brace_close = (r'\}', Token[None], None)

    # Operators
    shift_left = (r'<<', Token[None], None)
    shift_right = (r'>>', Token[None], None)
    equal = (r'==', Token[None], None)
    not_equal = (r'!=', Token[None], None)
    less_equal = (r'<=', Token[None], None)
    greater_equal = (r'>=', Token[None], None)

    # Single character operators
    plus = (r'\+', Token[None], None)
    minus = (r'-', Token[None], None)
    star = (r'\*', Token[None], None)
    slash = (r'/', Token[None], None)
    percent = (r'%', Token[None], None)
    ampersand = (r'&', Token[None], None)
    pipe = (r'\|', Token[None], None)
    caret = (r'\^', Token[None], None)
    less = (r'<', Token[None], None)
    greater = (r'>', Token[None], None)

    # Delimiters
    comma = (r',', Token[None], None)
    colon = (r':', Token[None], None)
    dot = (r'\.', Token[None], None)
    assign = (r'=', Token[None], None)

    # Whitespace
    whitespace = (r'[ \t]+', Token[None], None)
    newline = (r'\n', Token[None], None)

    def __init__(self, regex: str, token_class: type[Token], value_from_lexeme: Optional[Callable[[str], Any]]) -> None:
        self.pattern: Final[re.Pattern[str]] = re.compile(regex)
        self._token_class: Final[type[Token]] = token_class
        self._value_from_lexeme = value_from_lexeme

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
    def logical_operators(cls) -> set[TokenType]:
        """All logical operator types"""
        return {cls.logical_not, cls.logical_and, cls.logical_or}

    @classmethod
    def keyword_types(cls) -> set[TokenType]:
        """All keyword types"""
        return {
            cls.keyword_pub, cls.keyword_var, cls.keyword_def, cls.keyword_fn, cls.keyword_sig,
            cls.keyword_struct, cls.keyword_if, cls.keyword_else, cls.keyword_loop,
            cls.keyword_return, cls.keyword_break, cls.keyword_continue, cls.keyword_undefined
        }

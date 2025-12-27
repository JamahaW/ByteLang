from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable
from typing import Final
from typing import Optional
from typing import final


@dataclass
class SourcePosition:
    """Source code position"""

    name: str
    cursor: int
    line: int
    col: int

    def clone(self) -> SourcePosition:
        """Make clone of position"""
        return SourcePosition(self.name, self.cursor, self.line, self.col)

    def new_line(self) -> None:
        """Move cursor to new line"""
        self.line += 1
        self.col = 1

    def __str__(self):
        return f"in '{self.name}' at {self.line}:{self.col} ({self.cursor})"


@final
class Token[T]:
    """Token"""

    def __init__(
            self,
            *,
            token_type: TokenType,
            value: T,
            source_position: SourcePosition
    ) -> None:
        self.type = token_type
        self.value: Final = value
        self.source_position: Final = source_position

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {repr(self.value)}, src={self.source_position})"


class TokenType(Enum):
    """Token Type"""

    # --- Literals ---
    literal_string = (r'\"(?:[^\"\\]|\\.)*\"', Token[str], lambda s: s[1:-1])
    """ "string" """

    literal_float_exp = (r'-?\d+(?:\.\d+)?[eE][-+]?\d+', Token[float], float)
    """ -12e-34 """

    literal_float = (r'-?\d+\.\d+', Token[float], float)
    """ -123.456 """

    literal_int_hex = (r'0x[0-9a-fA-F]+', Token[int], lambda s: int(s, 16))
    """ 0x67 """

    literal_int_dec = (r'-?\d+', Token[int], int)
    """ -123456 """

    literal_int_bin = (r'0b[01]+', Token[int], lambda s: int(s, 2))
    """ 0b1010 """

    literal_int_char = (r'\'(?:[^\'\\]|\\.)\'', Token[int], lambda s: ord(s[1:-1]))
    """ 'A' """

    # --- Brackets ---
    bracket_open_round = (r'\(', Token[None], None)
    """ ( """

    bracket_close_round = (r'\)', Token[None], None)
    """ ) """

    bracket_open_square = (r'\[', Token[None], None)
    """ [ """

    bracket_close_square = (r'\]', Token[None], None)
    """ ] """

    bracket_open_figure = (r'\{', Token[None], None)
    """ { """

    bracket_close_figure = (r'\}', Token[None], None)
    """ } """

    # --- Delimiters ---
    delimiter_dot = (r'\.', Token[None], None)
    """ . """

    delimiter_comma = (r',', Token[None], None)
    """ , """

    delimiter_colon = (r':', Token[None], None)
    """ : """

    delimiter_assign = (r'=', Token[None], None)
    """ = """

    delimiter_semicolon = (r';', Token[None], None)
    """ ; """

    delimiter_star = (r'\*', Token[None], None)
    """ * """

    # --- Others ---
    identifier = (r'[a-zA-Z_][a-zA-Z0-9_]*', Token[str], str)
    """ identifier """

    comment = (r'//.*', Token[str], str)
    """ // comment """

    whitespace = (r'[ \t]+', Token[None], None)
    """ whitespace """

    newline = (r'\n', Token[None], None)
    """ newline """

    def __init__(self, regex: str, token_class: type[Token], value_from_lexeme: Optional[Callable[[str], object]]) -> None:
        self.pattern: Final[re.Pattern[str]] = re.compile(regex)
        self._token_class: Final[type[Token]] = token_class
        self._value_from_lexeme = value_from_lexeme

    def make(self, lexeme: str, source_position: SourcePosition) -> Token:
        """Make token from source"""

        return self._token_class(
            token_type=self,
            value=None if self._value_from_lexeme is None else self._value_from_lexeme(lexeme),
            source_position=source_position,
        )

    def skip(self) -> bool:
        """Should this token be skipped?"""
        return self in (TokenType.comment, TokenType.whitespace)

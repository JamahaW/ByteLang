from __future__ import annotations
from __future__ import annotations
from __future__ import annotations
from __future__ import annotations

import math
import re
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Final
from typing import Generic
from typing import Iterable
from typing import Optional
from typing import TextIO
from typing import TypeVar

from bytelang.handlers import ErrorHandler
from bytelang.tools import ReprTool


class Regex:
    IDENTIFIER = r"[_a-zA-Z\d]+"
    CHAR = r"^'.'$"
    INTEGER = r"^[+-]?[1-9][\d_]+$"
    EXPONENT = r"^[-+]?\d+[.]\d+([eE][-+]?\d+)?$"
    HEX_VALUE = r"^0[xX][_\da-fA-F]+$"
    OCT_VALUE = r"^[+-]?0[_0-8]+$"
    BIN_VALUE = r"^0[bB][_01]+$"


_T = TypeVar("_T")


class BasicParser(ABC, Generic[_T]):
    """Базовый парсер bytelang"""

    COMMENT: Final[str] = "#"

    def run(self, file: TextIO) -> Iterable[_T]:
        """Проанализировать файл и вернуть список (что вернуть, уточняется в дочерних классах)"""

        for index, source_line in enumerate(file):
            clean_line = source_line.split(self.COMMENT)[0].strip()

            if clean_line:
                yield self._parseLine(index + 1, source_line, clean_line)

    @abstractmethod
    def _parseLine(self, index: int, source_line: str, clean_line: str) -> Optional[_T]:
        """Обработать чистую строчку кода и вернуть абстрактный токен"""


class StatementType(Enum):
    """Виды выражений"""

    DIRECTIVE_USE = f"[.]{Regex.IDENTIFIER}"
    """Использование директивы"""
    MARK_DECLARE = f"{Regex.IDENTIFIER}:"
    """Установка метки"""
    INSTRUCTION_CALL = Regex.IDENTIFIER
    """Вызов инструкции"""

    def __repr__(self) -> str:
        return self.name


@dataclass(frozen=True, kw_only=True)
class StatementArgument:
    """Универсальный тип для значения аргумента"""

    integer: Optional[int]
    exponent: Optional[float]
    identifier: Optional[str]

    @staticmethod
    def fromName(name: str) -> StatementArgument:
        return StatementArgument(integer=None, exponent=None, identifier=name)

    @staticmethod
    def fromInteger(value: int) -> StatementArgument:
        return StatementArgument(integer=value, exponent=float(value), identifier=None)

    @staticmethod
    def fromExponent(value: float) -> StatementArgument:
        return StatementArgument(integer=math.floor(value), exponent=value, identifier=None)

    def __repr__(self) -> str:
        if self.identifier is None:
            return f"{{{self.integer} | {self.exponent}}}"

        return f"{self.identifier!r}"


@dataclass(frozen=True, kw_only=True)
class Statement:
    type: StatementType
    source_line: str
    clean_line: str
    line_index: int
    head: str
    lexemes: tuple[Optional[StatementArgument], ...]

    def __str__(self) -> str:
        type_index = f"{self.type.name}{f'@{self.line_index}':<5}"
        heap_lexemes = self.head + (ReprTool.iter(self.lexemes) if self.type is not StatementType.MARK_DECLARE else "")
        return f"{self.source_line.strip():32} {type_index:32} {heap_lexemes}"


class Parser(BasicParser[Statement]):

    def __init__(self, error_handler: ErrorHandler):
        self.__err = error_handler.getChild(self.__class__.__name__)

    def _parseLine(self, index: int, source_line: str, clean_line: str) -> Optional[Statement]:
        first, *lexemes = clean_line.split()

        self.__err.begin()

        args = tuple(self.__matchStatementArg(lexeme, i, index, source_line) for i, lexeme in enumerate(lexemes))
        _type, head = self.__matchStatementType(first, index, source_line)

        if self.__err.failed():
            return

        return Statement(type=_type, source_line=source_line, clean_line=clean_line, line_index=index, head=head, lexemes=args)

    def __matchStatementType(self, lexeme: str, index: int, line_source: str) -> tuple[StatementType, str] | tuple[None, None]:
        for statement_type in StatementType:
            if m := re.fullmatch(statement_type.value, lexeme):
                w = re.search(Regex.IDENTIFIER, m.string)
                return statement_type, w.string[w.start():w.end()]

        self.__err.writeLineAt(line_source, index, f"Не удалось определить тип выражения: '{lexeme}'")
        return None, None

    # FIXME каскад if
    def __matchStatementArg(self, lexeme: str, i: int, line_index: int, line_source: str) -> Optional[StatementArgument]:
        if re.match(Regex.INTEGER, lexeme):
            return StatementArgument.fromInteger(int(lexeme, 10))

        if re.match(Regex.BIN_VALUE, lexeme):
            return StatementArgument.fromInteger(int(lexeme, 2))

        if re.match(Regex.OCT_VALUE, lexeme):
            return StatementArgument.fromInteger(int(lexeme, 8))

        if re.match(Regex.HEX_VALUE, lexeme):
            return StatementArgument.fromInteger(int(lexeme, 16))

        if re.match(Regex.EXPONENT, lexeme):
            return StatementArgument.fromExponent(float(lexeme))

        if re.match(Regex.CHAR, lexeme):
            return StatementArgument.fromInteger(ord(lexeme[1]))  # 'c'

        if re.fullmatch(Regex.IDENTIFIER, lexeme):
            return StatementArgument.fromName(lexeme)

        self.__err.writeLineAt(line_source, line_index, f"Запись Аргумента ({i}) '{lexeme}' не распознана")

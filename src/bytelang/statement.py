from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from enum import Flag
from enum import auto
from typing import Optional

from bytelang.tools import ReprTool


class Regex:
    IDENTIFIER = r"^[a-zA-Z_][a-zA-Z\d_]*$"
    CHAR = r"^'.'$"
    INTEGER = r"^0$|^([+-]?[1-9][\d_]*)$"
    EXPONENT = r"^[-+]?\d+[.]\d+([eE][-+]?\d+)?$"
    HEX_VALUE = r"^0[xX][_\da-fA-F]+$"
    OCT_VALUE = r"^[+-]?0[_0-7]+$"
    BIN_VALUE = r"^0[bB][_01]+$"

    NAME = r"[_a-zA-Z\d]+"


class StatementType(Enum):
    """Виды выражений"""

    DIRECTIVE_USE = f"[.]{Regex.NAME}"
    """Использование директивы"""
    MARK_DECLARE = f"{Regex.NAME}:"
    """Установка метки"""
    INSTRUCTION_CALL = Regex.NAME
    """Вызов инструкции"""

    def __repr__(self) -> str:
        return self.name


class ArgumentValueType(Flag):
    """Значения, которые есть в аргументе"""
    INTEGER = auto()
    EXPONENT = auto()
    IDENTIFIER = auto()

    NUMBER = INTEGER | EXPONENT
    ANY = IDENTIFIER | NUMBER


@dataclass(frozen=True, kw_only=True)
class UniversalArgument:
    """Универсальный тип для значения аргумента"""

    type: ArgumentValueType
    integer: Optional[int]
    exponent: Optional[float]
    identifier: Optional[str]

    @staticmethod
    def fromName(name: str) -> UniversalArgument:
        return UniversalArgument(type=ArgumentValueType.IDENTIFIER, integer=None, exponent=None, identifier=name)

    @staticmethod
    def fromInteger(value: int) -> UniversalArgument:
        return UniversalArgument(type=ArgumentValueType.NUMBER, integer=value, exponent=float(value), identifier=None)

    @staticmethod
    def fromExponent(value: float) -> UniversalArgument:
        return UniversalArgument(type=ArgumentValueType.NUMBER, integer=math.floor(value), exponent=value, identifier=None)

    def __repr__(self) -> str:
        if self.identifier is None:
            return f"{{ {self.integer} | {self.exponent} }}"

        return f"<{self.identifier}>"


@dataclass(frozen=True, kw_only=True)
class Statement:
    type: StatementType
    line: str
    index: int
    head: str
    arguments: tuple[Optional[UniversalArgument], ...]

    def __str__(self) -> str:
        type_index = f"{self.type.name}{f'@{self.index}':<5}"
        heap_lexemes = self.head + (ReprTool.iter(self.arguments) if self.type is not StatementType.MARK_DECLARE else "")
        return f"{self.line:32} {type_index:32} {heap_lexemes}"

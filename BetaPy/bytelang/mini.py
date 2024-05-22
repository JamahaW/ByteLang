from __future__ import annotations

import enum
from dataclasses import dataclass

from .data import PointerVariable


class StatementType(enum.Enum):
    DIRECTIVE = enum.auto()
    MARK = enum.auto()
    INSTRUCTION = enum.auto()


@dataclass(frozen=True, eq=False)
class Statement:
    """Выражение"""

    type: StatementType
    lexeme: str
    args: tuple[str, ...]
    line: int
    source_line: str


@dataclass(frozen=True)
class DirectiveUnit:
    name: str
    arg_count: int | None


@dataclass(frozen=True, kw_only=True)
class DirectivesCollection:
    SET_HEAP: DirectiveUnit
    INIT_POINTER: DirectiveUnit
    USE_INLINE: DirectiveUnit
    DEFINE_MACRO: DirectiveUnit
    USE_PLATFORM: DirectiveUnit
    USE_PACKAGE: DirectiveUnit


@dataclass(frozen=True)
class CharSettings:
    COMMENT: str
    MARK: str
    DIRECTIVE: str


@dataclass(init=False)
class ProgramData:
    heap_size: int = 0
    constants = dict[str, int | str]()
    variables = dict[str, PointerVariable]()
    addr_vars = dict[int, PointerVariable]()

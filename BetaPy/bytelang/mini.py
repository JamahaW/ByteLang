from __future__ import annotations

import enum
from dataclasses import dataclass


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

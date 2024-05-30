from __future__ import annotations

import enum
from dataclasses import dataclass

from .tools import ReprTool


class StatementType(enum.Enum):
    DIRECTIVE = "directive"
    MARK = "mark"
    INSTRUCTION = "instruction"


@dataclass(frozen=True, eq=False)
class Statement:
    """Выражение"""

    type: StatementType
    lexeme: str
    args: tuple[str, ...]
    line: int
    source_line: str

    def __str__(self) -> str:
        mark_index = f"{self.type.value:12}{f'@{self.line}':<5}"
        lexeme_args = f"{self.lexeme}" + (ReprTool.iter(self.args) if self.type is not StatementType.MARK else "")
        return f"{mark_index} {lexeme_args:<32} {self.source_line}"

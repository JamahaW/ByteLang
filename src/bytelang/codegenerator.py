from dataclasses import dataclass
from typing import Any
from typing import Iterable

from bytelang.content import EnvironmentInstruction
from bytelang.parsers import Statement


@dataclass(frozen=True, kw_only=True)
class CodeInstruction:
    instruction: EnvironmentInstruction
    arguments: tuple[Any, ...]  # TODO специальный объект, более конкретные или общие значения


class CodeGenerator:
    """
    Исполнитель Директив. # TODO нужен исполнитель директив

    Генератор промежуточного кода.
    Вычисление констант.

    Оптимизация
    """

    def run(self, statements: Iterable[Statement]) -> Iterable[CodeInstruction]:
        pass

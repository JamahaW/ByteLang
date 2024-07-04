from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Callable
from typing import ClassVar
from typing import Final
from typing import Generic
from typing import Iterable
from typing import Optional
from typing import TextIO
from typing import TypeVar

from bytelang.handlers import BasicErrorHandler
from bytelang.statement import Regex
from bytelang.statement import Statement
from bytelang.statement import StatementType
from bytelang.statement import UniversalArgument
from bytelang.tools import Filter

_T = TypeVar("_T")


class Parser(ABC, Generic[_T]):
    """Базовый парсер bytelang"""

    COMMENT: Final[str] = "#"

    def run(self, file: TextIO) -> Iterable[_T]:
        return Filter.notNone(
            self._parseLine(index + 1, line)
            for index, line in enumerate(filter(bool, map(self.__cleanup, file)))
        )

    def __cleanup(self, line: str) -> str:
        return line.split(self.COMMENT)[0].strip()

    @abstractmethod
    def _parseLine(self, index: int, line: str) -> Optional[_T]:
        """Обработать чистую строчку кода и вернуть абстрактный токен"""


@dataclass(frozen=True)
class Matcher:
    __pattern: str
    __handler: Callable[[str], UniversalArgument]

    def process(self, lexeme: str) -> Optional[UniversalArgument]:
        if re.match(self.__pattern, lexeme):
            return self.__handler(lexeme)


class StatementParser(Parser[Statement]):
    __MATCHERS: ClassVar[tuple[Matcher, ...]] = (
        Matcher(Regex.INTEGER, lambda s: UniversalArgument.fromInteger(int(s, 10))),
        Matcher(Regex.BIN_VALUE, lambda s: UniversalArgument.fromInteger(int(s, 2))),
        Matcher(Regex.OCT_VALUE, lambda s: UniversalArgument.fromInteger(int(s, 8))),
        Matcher(Regex.HEX_VALUE, lambda s: UniversalArgument.fromInteger(int(s, 16))),
        Matcher(Regex.EXPONENT, lambda s: UniversalArgument.fromExponent(float(s))),
        Matcher(Regex.CHAR, lambda s: UniversalArgument.fromExponent(ord(s[1]))),
        Matcher(Regex.IDENTIFIER, lambda s: UniversalArgument.fromName(s)),
    )

    def __init__(self, error_handler: BasicErrorHandler):
        self.__err = error_handler.getChild(self.__class__.__name__)

    def _parseLine(self, index: int, line: str) -> Optional[Statement]:
        first, *lexemes = line.split()

        self.__err.begin()

        args = tuple(self.__matchStatementArg(lexeme, i, index, line) for i, lexeme in enumerate(lexemes))
        _type, head = self.__matchStatementType(first, index, line)

        if self.__err.failed():
            return

        return Statement(type=_type, line=line, index=index, head=head, arguments=args)

    def __matchStatementType(self, lexeme: str, index: int, line_source: str) -> tuple[StatementType, str] | tuple[None, None]:
        for statement_type in StatementType:
            if m := re.fullmatch(statement_type.value, lexeme):
                w = re.search(Regex.NAME, m.string)
                return statement_type, w.string[w.start():w.end()]

        self.__err.writeLineAt(line_source, index, f"Не удалось определить тип выражения: '{lexeme}'")
        return None, None

    def __matchStatementArg(self, lexeme: str, i: int, line_index: int, line_source: str) -> Optional[UniversalArgument]:
        for matcher in self.__MATCHERS:
            if ret := matcher.process(lexeme):
                return ret

        self.__err.writeLineAt(line_source, line_index, f"Запись Аргумента ({i}) '{lexeme}' не распознана")

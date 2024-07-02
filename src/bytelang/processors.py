import re
from dataclasses import dataclass
from enum import Enum
from os import PathLike
from typing import Final
from typing import Iterable
from typing import Optional
from typing import TextIO

from bytelang.handlers import ErrorHandler
from bytelang.registries import EnvironmentsRegistry
from bytelang.registries import PackageRegistry
from bytelang.registries import PrimitiveTypeRegistry
from bytelang.registries import ProfileRegistry
from bytelang.tools import ReprTool


class Token:
    CHAR_DIRECTIVE = "."
    CHAR_MARK = ":"


class Regex:
    VALID_WORD = r"[_a-zA-Z\d]+"
    INTEGER = r"^[+-]?[\d_]+$"
    HEX_VALUE = r"^0[xX][_\da-fA-F]+$"
    BIN_VALUE = r"^0[bB][_\da-fA-F]+$"


class StatementType(Enum):
    """
    Виды выражений
    """

    DIRECTIVE_USE = f"[{Token.CHAR_DIRECTIVE}]{Regex.VALID_WORD}[^{Token.CHAR_MARK}]"
    """Использование директивы"""
    MARK_DECLARE = f"{Regex.VALID_WORD}{Token.CHAR_MARK}"
    """Установка метки"""
    INSTRUCTION_CALL = Regex.VALID_WORD
    """Вызов инструкции"""

    def __repr__(self) -> str:
        return self.name


# @dataclass(frozen=True, kw_only=True)
# class StatementArgument:
#     integer: Optional[int]
#     identifier: Optional[str]


@dataclass(frozen=True, kw_only=True)
class Statement:
    type: StatementType
    source_line: str
    source_line_clean: str
    source_line_index: int
    head: str
    lexemes: tuple[Optional[str | int], ...]  # TODO нужен какой-то универсальный тип для значения (StatementArgument)

    def __str__(self) -> str:
        type_index = f"{self.type.name}{f'@{self.source_line_index}':<5}"
        heap_lexemes = self.head + (ReprTool.iter(self.lexemes) if self.type is not StatementType.MARK_DECLARE else "")
        return f"{type_index:32} {heap_lexemes:<32} {self.source_line.strip()}"


class LexicalAnalyzer:
    COMMENT: Final[str] = "#"

    def __init__(self, error_handler: ErrorHandler):
        self.__err = error_handler.getChild(self.__class__.__name__)

    def run(self, file: TextIO) -> Iterable[Statement]:
        return filter((lambda s: s is not None), (
            self.__process(line, raw_source_line, i + 1)
            for i, raw_source_line in enumerate(file)
            if (line := raw_source_line.split(self.COMMENT)[0].strip())
        ))

    def __process(self, line: str, raw_line: str, index: int) -> Optional[Statement]:
        first, *lexemes = line.split()

        self.__err.begin()

        args = tuple(self.__matchStatementArg(lexeme, i, index, raw_line) for i, lexeme in enumerate(lexemes))
        statement_type, head = self.__matchStatementType(first, index, raw_line)

        if self.__err.failed():
            return

        return Statement(
            type=statement_type,
            source_line=raw_line,
            source_line_clean=line,
            source_line_index=index,
            head=head,
            lexemes=args
        )

    def __matchStatementType(self, lexeme: str, index: int, raw_line: str) -> tuple[StatementType, str] | tuple[None, None]:
        for statement_type in StatementType:
            if m := re.fullmatch(statement_type.value, lexeme):
                w = re.search(Regex.VALID_WORD, m.string)
                return statement_type, w.string[w.start():w.end()]

        self.__err.writeLineAt(raw_line, index, f"Не удалось определить тип выражения: '{lexeme}'")
        return None, None

    def __matchStatementArg(self, lexeme: str, arg_i: int, index: int, raw_line: str) -> Optional[str | int]:
        if re.match(Regex.INTEGER, lexeme):
            return int(lexeme, 10)

        if re.match(Regex.BIN_VALUE, lexeme):
            return int(lexeme, 2)

        if re.match(Regex.HEX_VALUE, lexeme):
            return int(lexeme, 16)

        if re.fullmatch(Regex.VALID_WORD, lexeme):
            return lexeme

        self.__err.writeLineAt(raw_line, index, f"Запись Аргумента ({arg_i}) '{lexeme}' не распознана")


class Compiler:
    """
    API byteLang
    """

    def __init__(self) -> None:
        self.__primitive_type_registry = PrimitiveTypeRegistry()
        self.__profile_registry = ProfileRegistry("json", self.__primitive_type_registry)
        self.__package_registry = PackageRegistry("blp", self.__primitive_type_registry)
        self.__environment_registry = EnvironmentsRegistry("json", self.__profile_registry, self.__package_registry)
        # TODO остальные реестры

        self.__error_handler = ErrorHandler()
        self.__lexical_analyzer = LexicalAnalyzer(self.__error_handler)

    def run(self, source_file: PathLike | str) -> bool:
        """
        Скомпилировать исходный код bls в байткод программу
        :param source_file: Путь к исходному файлу.
        :return Компиляция была завершена успешно (True)
        """

        with open(source_file) as f:
            statements = self.__lexical_analyzer.run(f)

            print(ReprTool.column(statements))

        # TODO доделать

        return self.__error_handler.success()

    def setPrimitivesFile(self, filepath: PathLike | str) -> None:
        """
        Указать путь к файлу настройки примитивных типов
        :param filepath:
        """
        self.__primitive_type_registry.setFile(filepath)

    def setEnvironmentsFolder(self, folder: PathLike | str) -> None:
        """
        Указать путь к папке окружений
        :param folder:
        """
        self.__environment_registry.setFolder(folder)

    def setPackagesFolder(self, folder: PathLike | str) -> None:
        """
        Указать путь к папке пакетов инструкций
        :param folder:
        """
        self.__package_registry.setFolder(folder)

    def setProfilesFolder(self, folder: PathLike | str) -> None:
        """
        Указать путь к папке профилей
        :param folder:
        """
        self.__profile_registry.setFolder(folder)

    def getProgram(self) -> Optional[bytes]:
        """
        Получить скомпилированный байткод.
        :return скомпилированный байткод. None Если программа не была скомпилирована
        """

    def getErrorsLog(self) -> Optional[str]:
        """
        Получить логи ошибок.
        :return лог ошибок или None, если ошибок не было
        """
        if not self.__error_handler.success():
            return self.__error_handler.getLog()

    def getInfoLog(self) -> str:
        """
        Получить подробную информацию о компиляции
        """

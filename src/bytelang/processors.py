from __future__ import annotations

from dataclasses import dataclass
from enum import Flag
from enum import auto
from os import PathLike
from typing import Iterable
from typing import Optional

from bytelang.bytecodegenerator import ByteCodeGenerator
from bytelang.codegenerator import CodeGenerator
from bytelang.codegenerator import CodeInstruction
from bytelang.codegenerator import ProgramData
from bytelang.content import PrimitiveType
from bytelang.handlers import BasicErrorHandler
from bytelang.handlers import ErrorHandler
from bytelang.parsers import StatementParser
from bytelang.registries import EnvironmentsRegistry
from bytelang.registries import PackageRegistry
from bytelang.registries import PrimitiveTypeRegistry
from bytelang.registries import ProfileRegistry
from bytelang.statement import Statement
from bytelang.tools import ReprTool
from bytelang.tools import StringBuilder


class LogInfo(Flag):
    """Флаги вывода логов компиляции"""
    PRIMITIVES = auto()
    """Вывести данные реестра примитивных типов"""
    ENVIRONMENT_INSTRUCTIONS = auto()
    """Вывести инструкции окружения"""
    PROFILE = auto()
    """Вывести данные профиля"""
    REGISTRIES = PRIMITIVES | ENVIRONMENT_INSTRUCTIONS | PROFILE
    """Вывести все доступные реестры"""

    STATEMENTS = auto()
    """Представление выражений"""
    CODE_INSTRUCTIONS = auto()
    """Представление инструкций промежуточного кода"""
    PARSER_RESULTS = CODE_INSTRUCTIONS | STATEMENTS
    """Весь парсинг"""

    VARIABLES = auto()
    """Представление переменных"""
    CONSTANTS = auto()
    """Значения констант"""
    PROGRAM_VALUES = VARIABLES | CONSTANTS
    """Все значения"""

    BYTECODE = auto()
    """Читаемый вид байт-кода"""

    ALL = REGISTRIES | PARSER_RESULTS | PROGRAM_VALUES | BYTECODE
    """Всё и сразу"""


@dataclass(frozen=True, kw_only=True, repr=False)
class CompileResult:
    primitives: Iterable[PrimitiveType]
    statements: tuple[Statement, ...]
    instructions: tuple[CodeInstruction, ...]
    program_data: ProgramData
    bytecode: bytes
    filepath: str

    def getInfoLog(self, flags: LogInfo = LogInfo.ALL) -> str:
        sb = StringBuilder()
        env = self.program_data.environment

        if LogInfo.PRIMITIVES in flags:
            sb.append(ReprTool.headed("primitives", self.primitives, _repr=True))

        if LogInfo.ENVIRONMENT_INSTRUCTIONS in flags:
            sb.append(ReprTool.headed(f"instructions : {env.name}", env.instructions.values()))

        if LogInfo.PROFILE in flags:
            sb.append(ReprTool.title(f"profile : {env.profile.name}")).append(ReprTool.strDict(env.profile.__dict__, _repr=True))

        if LogInfo.STATEMENTS in flags:
            sb.append(ReprTool.headed(f"statements : {self.filepath}", self.statements))

        if LogInfo.CONSTANTS in flags:
            sb.append(ReprTool.title("constants")).append(ReprTool.strDict(self.program_data.constants))

        if LogInfo.VARIABLES in flags:
            sb.append(ReprTool.headed("variables", self.program_data.variables))

        if LogInfo.CODE_INSTRUCTIONS in flags:
            sb.append(ReprTool.headed(f"code instructions : {self.filepath}", self.instructions))

        return sb.toString()


class Compiler:
    """Компилятор ByteLang"""

    def __init__(self, error_handler: BasicErrorHandler, primitives: PrimitiveTypeRegistry, environments: EnvironmentsRegistry):
        self.__err = error_handler.getChild(self.__class__.__name__)
        self.__primitives = primitives
        self.__parser = StatementParser(self.__err)
        self.__code_generator = CodeGenerator(self.__err, environments, primitives)
        self.__bytecode_generator = ByteCodeGenerator(self.__err)

    def run(self, source_filepath: PathLike | str) -> Optional[CompileResult]:
        with open(source_filepath) as f:
            statements = tuple(self.__parser.run(f))

        instructions, data = self.__code_generator.run(statements)
        program = self.__bytecode_generator.run(instructions, data)

        if self.__err.success():
            return CompileResult(
                primitives=self.__primitives.getValues(),
                statements=statements,
                instructions=instructions,
                program_data=data,
                bytecode=program,
                filepath=str(source_filepath)
            )


class ByteLang:
    """API byteLang"""

    def __init__(self) -> None:
        self.__primitive_type_registry = PrimitiveTypeRegistry()
        self.__profile_registry = ProfileRegistry("json", self.__primitive_type_registry)
        self.__package_registry = PackageRegistry("blp", self.__primitive_type_registry)
        self.__environment_registry = EnvironmentsRegistry("json", self.__profile_registry, self.__package_registry)
        self.__errors_handler = ErrorHandler()
        self.__compiler = Compiler(self.__errors_handler, self.__primitive_type_registry, self.__environment_registry)

    def compile(self, source_filepath: PathLike | str) -> Optional[CompileResult]:
        """
        Скомпилировать исходный код bls в байткод программу
        :param source_filepath: Путь к исходному файлу.
        """
        self.__errors_handler.reset()
        return self.__compiler.run(source_filepath)

    def setPrimitivesFile(self, filepath: PathLike | str) -> None:
        """Указать путь к файлу настройки примитивных типов"""
        self.__primitive_type_registry.setFile(filepath)

    def setEnvironmentsFolder(self, folder: PathLike | str) -> None:
        """Указать путь к папке окружений"""
        self.__environment_registry.setFolder(folder)

    def setPackagesFolder(self, folder: PathLike | str) -> None:
        """Указать путь к папке пакетов инструкций"""
        self.__package_registry.setFolder(folder)

    def setProfilesFolder(self, folder: PathLike | str) -> None:
        """Указать путь к папке профилей"""
        self.__profile_registry.setFolder(folder)

    def getErrorsLog(self) -> Optional[str]:
        """
        Получить логи ошибок.
        :return лог ошибок или None, если ошибок не было
        """
        if not self.__errors_handler.success():
            return self.__errors_handler.getLog()

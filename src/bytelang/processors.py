from __future__ import annotations

from dataclasses import dataclass
from enum import Flag
from enum import auto
from os import PathLike
from typing import Iterable
from typing import Optional

from bytelang.codegenerator import ByteCodeGenerator
from bytelang.codegenerator import CodeGenerator
from bytelang.codegenerator import CodeInstruction
from bytelang.codegenerator import ProgramData
from bytelang.content import PrimitiveType
from bytelang.handlers import BasicErrorHandler
from bytelang.parsers import Parser
from bytelang.parsers import StatementParser
from bytelang.registries import EnvironmentsRegistry
from bytelang.registries import PrimitiveTypeRegistry
from bytelang.statement import Statement
from bytelang.tools import FileTool
from bytelang.tools import ReprTool
from bytelang.tools import StringBuilder


class LogFlag(Flag):
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
    source_filepath: str
    bytecode_filepath: str

    def getInfoLog(self, flags: LogFlag = LogFlag.ALL) -> str:
        sb = StringBuilder()
        env = self.program_data.environment

        if LogFlag.PRIMITIVES in flags:
            sb.append(ReprTool.headed("primitives", self.primitives, _repr=True))

        if LogFlag.ENVIRONMENT_INSTRUCTIONS in flags:
            sb.append(ReprTool.headed(f"instructions : {env.name}", env.instructions.values()))

        if LogFlag.PROFILE in flags:
            sb.append(ReprTool.title(f"profile : {env.profile.name}")).append(ReprTool.strDict(env.profile.__dict__, _repr=True))

        if LogFlag.STATEMENTS in flags:
            sb.append(ReprTool.headed(f"statements : {self.source_filepath}", self.statements))

        if LogFlag.CONSTANTS in flags:
            sb.append(ReprTool.title("constants")).append(ReprTool.strDict(self.program_data.constants))

        if LogFlag.VARIABLES in flags:
            sb.append(ReprTool.headed("variables", self.program_data.variables))

        if LogFlag.CODE_INSTRUCTIONS in flags:
            sb.append(ReprTool.headed(f"code instructions : {self.source_filepath}", self.instructions))

        if LogFlag.BYTECODE in flags:
            self.__writeByteCode(sb)

        return sb.toString()

    @staticmethod
    def __writeComment(sb: StringBuilder, message: object) -> None:
        sb.append(f"\n{Parser.COMMENT}  {message}")

    def __writeByteCode(self, sb: StringBuilder) -> None:
        ins_by_addr = {ins.address: ins for ins in self.instructions}
        var_by_addr = {var.address: var for var in self.program_data.variables}

        sb.append(ReprTool.title(f"bytecode view : {self.bytecode_filepath}"))

        for address, byte in enumerate(self.bytecode):
            if address == 0:
                self.__writeComment(sb, "program start address define")

            if (var := var_by_addr.get(address)) is not None:
                self.__writeComment(sb, var)

            if (mark := self.program_data.marks.get(address)) is not None:
                self.__writeComment(sb, f"{mark}:")

            if (ins := ins_by_addr.get(address)) is not None:
                self.__writeComment(sb, ins)

            sb.append(f"{address:04}: {byte:02X}")


class Compiler:
    """Компилятор ByteLang"""

    def __init__(self, error_handler: BasicErrorHandler, primitives: PrimitiveTypeRegistry, environments: EnvironmentsRegistry):
        self.__err = error_handler.getChild(self.__class__.__name__)
        self.__primitives = primitives
        self.__parser = StatementParser(self.__err)
        self.__code_generator = CodeGenerator(self.__err, environments, primitives)
        self.__bytecode_generator = ByteCodeGenerator(self.__err)

    def run(self, source_filepath: PathLike | str, bytecode_filepath: PathLike | str) -> Optional[CompileResult]:
        with open(source_filepath) as f:
            statements = tuple(self.__parser.run(f))

        instructions, data = self.__code_generator.run(statements)

        if not (program := self.__bytecode_generator.run(instructions, data)):
            return

        if not self.__err.success():
            return

        FileTool.saveBytes(bytecode_filepath, program)

        return CompileResult(
            primitives=self.__primitives.getValues(),
            statements=statements,
            instructions=instructions,
            program_data=data,
            bytecode=program,
            source_filepath=str(source_filepath),
            bytecode_filepath=str(bytecode_filepath)
        )

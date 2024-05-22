from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Iterable, Optional, Callable

from .data import Package, Platform, Argument, PointerVariable, InstructionUnit
from .errors import ByteLangError, LexicalError, CodeGenerationError, CompileError
from .loaders import PackageLoader, PlatformLoader
from .mini import StatementType, Statement
from .primitives import PrimitiveCollection


class Environment:
    @dataclass(frozen=True)
    class CharSettings:
        COMMENT: str
        MARK: str
        DIRECTIVE: str

    @dataclass(init=False)
    class ProgramData:
        heap_head_value: int = 0
        constants = dict[str, int | str]()
        variables = dict[str, PointerVariable]()
        addr_vars = dict[bytes, PointerVariable]()

    def __init__(self, packages: PackageLoader, platforms: PlatformLoader):
        self.packages = packages
        self.platforms = platforms

        self.program = Environment.ProgramData()

        self.CHAR = Environment.CharSettings('#', ':', '.')

    def getPlatform(self) -> Platform:
        return self.platforms.get()

    def getPackage(self) -> Package:
        return self.packages.get()


# TODO Lexical, Syntax??
class LexicalAnalyser:

    def __init__(self, environment: Environment):
        self.environment = environment

    def run(self, source: str) -> Iterable[Statement]:
        ret = list()

        for index, source_line in enumerate(source.split("\n")):
            if (line_no_comment := source_line.split(self.environment.CHAR.COMMENT)[0].strip()) != "":
                ret.append(self.__createStatement(index, line_no_comment, source_line))

        return ret

    def __createStatement(self, index: int, line_clean: str, source_line: str):
        lexeme, *args = line_clean.split()
        _type = None

        if lexeme[-1] == self.environment.CHAR.MARK:
            _type = StatementType.MARK
            lexeme = lexeme[:-1]

        elif lexeme[0] == self.environment.CHAR.DIRECTIVE:
            lexeme = lexeme[1:]
            _type = StatementType.DIRECTIVE

        elif not lexeme[0].isdigit() and lexeme.isalnum():
            _type = StatementType.INSTRUCTION

        else:
            raise LexicalError(f"Invalid Statement: '{lexeme}' at Line {index}\n'{source_line}'")

        return Statement(_type, lexeme, args, index + 1, source_line)


class CodeGenerator:
    BASES_PREFIXES: dict[str, int] = {'x': 16, 'o': 8, 'b': 2}

    def __init__(self, environment: Environment):
        self.__env = environment

        self.__mark_offset: int = 0
        self.__ptr_addr_next: int = 0

        self.__used_heap_directive = False
        self.__used_package_directive = False
        self.__used_platform_directive = False

        self.__DIRECTIVES_TABLE: dict[str, tuple[Optional[int], Callable[[Statement], Optional[InstructionUnit]]]] = {
            "heap": (1, self.directiveSetHeap),
            "ptr": (3, self.directiveInitPointer),
            "inline": (None, self.directiveUseInline),
            "def": (2, self.directiveDefineMacro),
            "package": (1, self.directiveUsePackage),
            "platform": (1, self.directiveUsePlatform),
        }

    def run(self, statements: Iterable[Statement]) -> Iterable[InstructionUnit]:
        self.__mark_offset = 0

        ret = list[InstructionUnit]()

        for statement in statements:
            match statement.type:
                case StatementType.MARK:
                    self.mark(statement)

                case StatementType.DIRECTIVE:
                    if (u := self.directive(statement)) is not None:
                        ret.append(u)

                case StatementType.INSTRUCTION:
                    ret.append(self.instruction(statement))

        return ret

    def mark(self, statement: Statement):
        if not self.__used_platform_directive:
            raise CodeGenerationError(f'ParsingError MustUsePlatform : {statement}')

        self.__env.program.constants[statement.lexeme] = self.__mark_offset

    def getValue(self, arg_lexeme: str, arg_type: Argument) -> bytes:
        """Получить значение из лексемы"""

        # данное значение найдено среди констант
        if (val := self.__env.program.constants.get(arg_lexeme)) is not None:
            return self.getValue(val, arg_type)

        # если указатель - возвращаем адрес
        if (val := self.__env.program.variables.get(arg_lexeme)) is not None:
            return arg_type.toBytes(self.__env.getPlatform(), val.ptr)

        # ничего не было найдено, возможно это число

        base = 10

        if len(arg_lexeme) > 2 and arg_lexeme[0] == '0' and (base := self.BASES_PREFIXES.get(arg_lexeme[1])) is None:
            raise CodeGenerationError(f"IncorrectBasePrefix: {arg_lexeme}")

        try:
            return arg_type.toBytes(self.__env.getPlatform(), int(arg_lexeme, base))

        except ValueError as e:
            raise CodeGenerationError(f"NotValid value '{arg_lexeme}' error: {e}")

    def instruction(self, statement: Statement, inline_last: bool = False) -> InstructionUnit:
        instruction = self.__env.getPackage().INSTRUCTIONS.get(statement.lexeme)

        if instruction is None:
            raise CodeGenerationError(f'ParsingError{"InvalidInstruction"} : {statement}')

        if instruction.can_inline is False and inline_last is True:
            raise CodeGenerationError(f'ParsingError{"CantInline"} : {statement}')

        if len(instruction.signature) != len(statement.args):
            raise CodeGenerationError(f'ParsingError{"InvalidArgument"} : {statement}')

        self.__mark_offset += instruction.getSize(self.__env.getPlatform(), inline_last)

        return InstructionUnit(instruction, self.instructionValidateArg(statement, instruction.signature, inline_last), inline_last)

    def instructionValidateArg(self, statement: Statement, signature: tuple[Argument, ...], inline: bool) -> tuple[bytes, ...]:
        ret = list[bytes]()

        for index, (arg_type, arg_value) in enumerate(zip(signature, statement.args)):
            arg_value = self.getValue(arg_value, arg_type)
            if not inline and arg_type.pointer and arg_value not in self.__env.program.addr_vars.keys():
                raise CodeGenerationError(f'ParsingError{"AddrError"} : {statement}')

            ret.append(arg_value)

        return tuple(ret)

    def directive(self, statement: Statement) -> InstructionUnit | None:
        if (e := self.__DIRECTIVES_TABLE.get(statement.lexeme)) is None:
            raise CodeGenerationError(f'ParsingError{"InvalidDirective"} : {statement}')

        arg_count, func = e

        if arg_count is None or len(statement.args) == arg_count:
            return func(statement)

        raise CodeGenerationError(f'ParsingError{"InvalidArgCount"} : {statement}')

    def directiveUsePackage(self, statement: Statement):
        if self.__used_package_directive:
            raise CodeGenerationError(f'ParsingError{"PackageAlreadyUsed"} : {statement}')

        self.__used_package_directive = True
        self.__env.packages.use(statement.args[0])

    def directiveUsePlatform(self, statement: Statement):
        if self.__used_platform_directive:
            raise CodeGenerationError(f'ParsingError{"PlatformAlreadyUsed"} : {statement}')

        self.__used_platform_directive = True
        self.__env.platforms.use(statement.args[0])

        self.__mark_offset = self.__env.getPlatform().HEAP_PTR.size
        self.__ptr_addr_next = int(self.__mark_offset)

    def directiveDefineMacro(self, statement):
        name, value = statement.args
        self.__env.program.constants[name] = value

    def directiveUseInline(self, statement: Statement) -> InstructionUnit:
        lexeme, *args = statement.args
        return self.instruction(Statement(StatementType.INSTRUCTION, lexeme, args, statement.line, statement.source_line), True)

    def directiveInitPointer(self, statement: Statement):
        ptr_type, ptr_name, ptr_value = statement.args

        if (ptr_type := PrimitiveCollection.get(ptr_type)) is None:
            raise CodeGenerationError(f'ParsingError"InvalidType" : {statement}')

        ptr_addr = self.__ptr_addr_next

        if ptr_addr < self.__env.getPlatform().HEAP_PTR.size:
            raise CodeGenerationError(f'ParsingError"AddressBeforeHeap" : {statement}')

        # if (ptr_addr + ptr_type.size) > self.__env.program.heap_head_value:
        #     raise CodeGenerationError(f'ParsingError"AddressAfterHeap" : {statement}')

        p_vars = self.__env.program.variables

        if ptr_name in p_vars:
            raise CodeGenerationError(f'ParsingError"RedefineVariable" : {statement}')

        ptr_value = self.getValue(ptr_value, Argument(self.__env.getPlatform().HEAP_PTR, False))

        # if not (ptr_type.min <= ptr_value <= ptr_type.max):
        #     raise CodeGenerationError(f'ParsingErrorNotInRange[{ptr_type.min};{ptr_type.max}] : {statement}')

        ret = p_vars[ptr_name] = PointerVariable(ptr_name, ptr_addr, ptr_type, ptr_value)
        self.__env.program.addr_vars[self.__env.getPlatform().HEAP_PTR.toBytes(ptr_addr)] = ret
        self.__ptr_addr_next += ret.getSize(self.__env.getPlatform())

    def directiveSetHeap(self, statement: Statement):
        if self.__used_heap_directive:
            raise CodeGenerationError(f'ParsingError"ReinitHeap" : {statement}')

        self.__used_heap_directive = True
        self.__env.program.heap_head_value = self.getValue(statement.args[0], Argument(self.__env.getPlatform().HEAP_PTR, False))
        h = int(statement.args[0])  # TODO FIXME
        self.__mark_offset += h

        # if not (0 < h < self.__env.getPlatform().HEAP_PTR.max):
        #     raise CodeGenerationError(f'ParsingError"InvalidHeapSize" : {statement}')


class ProgramGenerator:
    """Компилятор в байткод"""

    def __init__(self, environment: Environment):
        self.environment = environment

    def run(self, statementsUnits: Iterable[InstructionUnit]) -> bytes:
        ret = self.__getHeap() + self.__getProgram(statementsUnits)

        if (L := len(ret)) > (max_len := self.environment.getPlatform().PROGRAM_LEN):
            raise CompileError(f"Program too long ({L}/{max_len})")

        return ret

    def __getProgram(self, statementsUnits: Iterable[InstructionUnit]):
        program = bytes()
        for unit in statementsUnits:
            program += unit.toBytes(self.environment.getPlatform())
        return program

    def __getHeap(self):
        h_ptr = self.environment.getPlatform().HEAP_PTR
        ptr_size = h_ptr.size
        size = self.environment.program.heap_head_value
        size = struct.unpack(h_ptr.format, size)[0]
        heap_data = PrimitiveCollection.pointer(ptr_size).toBytes(size + ptr_size)

        if size == 0:
            return heap_data

        heap_data = list(heap_data + bytes(size))

        for var in self.environment.program.variables.values():
            var_bytes = list(var.toBytes(self.environment.getPlatform()))
            for i, b in enumerate(var_bytes):
                heap_data[i + var.ptr] = b

        return bytes(heap_data)


class Compiler:

    def __init__(self, packages_folder: str, platforms_folder: str):
        self.environment = e = Environment(PackageLoader(packages_folder), PlatformLoader(platforms_folder))
        self.tokeniser = LexicalAnalyser(e)
        self.parser = CodeGenerator(e)
        self.compiler = ProgramGenerator(e)

        self.instruction_units: Optional[Iterable[Statement]] = None
        self.statements: Optional[Iterable[InstructionUnit]] = None

    def run(self, source: str) -> bytes:
        try:
            self.statements = self.tokeniser.run(source)
        except LexicalError as e:
            raise ByteLangError(e)

        try:
            self.instruction_units = self.parser.run(self.statements)
        except CodeGenerationError as e:
            raise ByteLangError(e)

        try:
            return self.compiler.run(self.instruction_units)
        except CompileError as e:
            raise ByteLangError(e)

from __future__ import annotations

from typing import Iterable, Optional, Callable

from .data import Package, Platform, Argument, PointerVariable, InstructionUnit
from .errors import ByteLangError, LexicalError, CodeGenerationError, CompileError
from .loaders import PackageLoader, PlatformLoader
from .mini import StatementType, Statement
from .primitives import PrimitiveCollection, PrimitiveType


class Environment:
    BASES_PREFIXES: dict[str, int] = {'x': 16, 'o': 8, 'b': 2}

    def __init__(self, packages: PackageLoader, platforms: PlatformLoader):
        self.packages = packages
        """Загрузчик пакетов инструкций"""
        self.platforms = platforms
        """Загрузчик платформ"""

        self.start: int = 0
        """Индекс байта начала кода"""
        self.consts = dict[str, str | int]()
        """значения макро констант"""
        self.variables = dict[str, PointerVariable]()
        """переменные"""
        self.addr_vars = set[bytes]()
        """множество адресов существующих переменных"""

    def getPlatform(self) -> Platform:
        return self.platforms.get()

    def getPackage(self) -> Package:
        return self.packages.get()

    def readConst(self, lexeme: str) -> int | float:
        # лексема - имя константы -> значение константы
        if (ret := self.consts.get(lexeme)) is not None:
            return self.readConst(ret)

        try:
            # лексема - float
            if "." in lexeme:
                return float(lexeme)

            # может быть int
            base = 10

            if len(lexeme) > 2 and lexeme[0] == '0' and (base := self.BASES_PREFIXES.get(lexeme[1])) is None:
                raise ByteLangError(f"IncorrectBasePrefix: {lexeme}")

            return int(lexeme, base)

        except ValueError as e:
            raise ByteLangError(f"cannot cast value '{lexeme}' to _type.name\n({e})")

    def writeValue(self, lexeme: str, _type: PrimitiveType) -> bytes:
        # лексема - имя переменной -> адрес переменной
        if (ret := self.variables.get(lexeme)) is not None:
            return self.getPlatform().HEAP_PTR.write(ret.address)

        # любое другое константное значение -> читаем константу
        return _type.write(self.readConst(lexeme))


# TODO Lexical, Syntax??
class LexicalAnalyser:

    def __init__(self, environment: Environment):
        self.environment = environment
        self.COMMENT = "#"
        self.MARK = ":"
        self.DIRECTIVE = "."

    def run(self, source: str) -> Iterable[Statement]:
        ret = list()

        for index, source_line in enumerate(source.split("\n")):
            if (line_no_comment := source_line.split(self.COMMENT)[0].strip()) != "":
                ret.append(self.__createStatement(index + 1, line_no_comment, source_line))

        return ret

    def __createStatement(self, index: int, line_clean: str, source_line: str):
        lexeme, *args = line_clean.split()
        _type = None

        if lexeme[-1] == self.MARK:
            _type = StatementType.MARK
            lexeme = lexeme[:-1]

        elif lexeme[0] == self.DIRECTIVE:
            lexeme = lexeme[1:]
            _type = StatementType.DIRECTIVE

        elif not lexeme[0].isdigit() and lexeme.isalnum():
            _type = StatementType.INSTRUCTION

        else:
            raise LexicalError(f"Invalid Statement: '{lexeme}' at Line {index}\n'{source_line}'")

        return Statement(_type, lexeme, args, index, source_line)


class CodeGenerator:

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

        self.__env.consts[statement.lexeme] = self.__mark_offset

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
            arg_value = self.__env.writeValue(arg_value, arg_type.datatype)
            if not inline and arg_type.pointer and arg_value not in self.__env.addr_vars:
                raise CodeGenerationError(f'ParsingErrorAddrError : {statement}')

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
        self.__env.consts[name] = value

    def directiveUseInline(self, statement: Statement) -> InstructionUnit:
        lexeme, *args = statement.args
        return self.instruction(Statement(StatementType.INSTRUCTION, lexeme, args, statement.line, statement.source_line), True)

    def directiveInitPointer(self, statement: Statement):
        _type, name, value_lexeme = statement.args

        if (_type := PrimitiveCollection.get(_type)) is None:
            raise CodeGenerationError(f'ParsingError"InvalidType" : {statement}')

        address = self.__ptr_addr_next

        if (address + _type.size) > self.__env.start:
            raise CodeGenerationError(f'ParsingError"AddressAfterHeap" : {statement}')

        if name in self.__env.variables:
            raise CodeGenerationError(f'ParsingError"RedefineVariable" : {statement}')

        value_bytes = self.__env.writeValue(value_lexeme, _type)
        value_lexeme = _type.read(value_bytes)

        if not (_type.min <= value_lexeme <= _type.max):
            raise CodeGenerationError(f'ParsingErrorNotInRange[{_type.min};{_type.max}] : {statement}')

        ret = self.__env.variables[name] = PointerVariable(name, address, _type, value_bytes)
        self.__env.addr_vars.add(self.__env.getPlatform().HEAP_PTR.write(address))
        self.__ptr_addr_next += ret.getSize(self.__env.getPlatform())

    def directiveSetHeap(self, statement: Statement):
        if self.__used_heap_directive:
            raise CodeGenerationError(f'ParsingError"ReinitHeap" : {statement}')

        self.__used_heap_directive = True

        platform = self.__env.getPlatform()
        h = self.__env.start = self.__env.readConst(statement.args[0])
        self.__mark_offset += h

        if not (0 < h < platform.HEAP_PTR.max):
            raise CodeGenerationError(f'ParsingError"InvalidHeapSize" : {statement}')


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
            program += unit.write(self.environment.getPlatform())
        return program

    def __getHeap(self):
        h_ptr = self.environment.getPlatform().HEAP_PTR
        size = self.environment.start
        heap_data = PrimitiveCollection.pointer(h_ptr.size).write(size + h_ptr.size)  # TODO wtf

        if size == 0:
            return heap_data

        heap_data = list(heap_data + bytes(size))

        for var in self.environment.variables.values():
            var_bytes = list(var.write(self.environment.getPlatform()))
            for i, b in enumerate(var_bytes):
                heap_data[i + var.address] = b

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

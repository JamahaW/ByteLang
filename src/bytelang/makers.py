from __future__ import annotations

from typing import Iterable, Optional, Callable

from .data import Package, Platform, Argument, PointerVariable, InstructionUnit
from .errors import ByteLangError, ByteLangCompileError
from .handlers import ErrorHandler
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
        self.addr_vars = set[int]()
        """множество адресов существующих переменных"""

    def getPlatform(self) -> Platform:
        return self.platforms.get()

    def getPackage(self) -> Package:
        return self.packages.get()

    def readConst(self, lexeme: str) -> int | float:
        # лексема - имя константы -> значение константы
        if (ret := self.consts.get(lexeme)) is not None:
            return self.readConst(ret)

        # лексема - имя переменной -> адрес переменной
        if (ret := self.variables.get(lexeme)) is not None:
            return ret.address

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

        # любое другое константное значение -> читаем константу
        return _type.write(self.readConst(lexeme))


# TODO Lexical, Syntax??
class LexicalAnalyser(ErrorHandler):

    def __init__(self, environment: Environment):
        super().__init__(self)
        self.environment = environment
        self.COMMENT = "#"
        self.MARK = ":"
        self.DIRECTIVE = "."

    def run(self, source: str) -> Iterable[Statement]:
        ret = list()

        for index, source_line in enumerate(source.split("\n")):
            if (line_no_comment := source_line.split(self.COMMENT)[0].strip()) != "":
                ret.append(self.__createStatement(index + 1, line_no_comment))

        return ret

    def __createStatement(self, index: int, line_clean: str):
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
            self.addErrorMessage(f"Invalid Statement: '{lexeme}'\t at Line {index}")

        return Statement(_type, lexeme, args, index, line_clean)


class CodeGenerator(ErrorHandler):

    def __init__(self, environment: Environment):
        super().__init__(self)
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

        self.__STATEMENT_TYPE_TABLE: dict[StatementType, Callable[[Statement], Optional[InstructionUnit]]] = {
            StatementType.MARK: self.mark,
            StatementType.DIRECTIVE: self.directive,
            StatementType.INSTRUCTION: self.instruction
        }

    def run(self, statements: Iterable[Statement]) -> Iterable[InstructionUnit]:
        self.__mark_offset = 0
        ret = list[InstructionUnit]()

        for statement in statements:
            if (u := self.__STATEMENT_TYPE_TABLE.get(statement.type)(statement)) is not None:
                ret.append(u)

        return ret

    def mark(self, statement: Statement):
        if not self.__used_platform_directive:
            self.errorStatement("MustUsePlatform", statement)
            return

        self.__env.consts[statement.lexeme] = self.__mark_offset

    def instruction(self, statement: Statement) -> Optional[InstructionUnit]:
        return self.instructionFull(statement, False)

    def instructionFull(self, statement: Statement, inline_last: bool) -> Optional[InstructionUnit]:
        instruction = self.__env.getPackage().INSTRUCTIONS.get(statement.lexeme)

        if instruction is None:
            self.errorStatement("InvalidInstruction", statement)
            return

        if instruction.can_inline is False and inline_last is True:
            self.errorStatement("CantInline", statement)
            return

        if len(instruction.signature) != len(statement.args):
            self.errorStatement("InvalidArgumentCount", statement)

        self.__mark_offset += instruction.getSize(self.__env.getPlatform(), inline_last)
        return InstructionUnit(instruction, self.instructionValidateArg(statement, instruction.signature, inline_last), inline_last)

    def instructionValidateArg(self, statement: Statement, signature: tuple[Argument, ...], inline: bool) -> Optional[tuple[bytes, ...]]:
        ret = list[bytes]()

        for index, (arg_state, arg_lexeme) in enumerate(zip(signature, statement.args)):
            arg_value = self.__env.readConst(arg_lexeme)
            arg_primitive = arg_state.getPrimitive(self.__env.getPlatform())

            if not ((mi := arg_primitive.min) < arg_value < (ma := arg_primitive.max)):
                self.errorStatement(f"InvalidValue {arg_lexeme} ({arg_value}) not in [{mi};{ma}]", statement)
                return

            if not inline and arg_state.pointer and arg_value not in self.__env.addr_vars:
                self.errorStatement("ParsingErrorAddrError", statement)
                return

            ret.append(arg_state.datatype.write(arg_value))

        return tuple(ret)

    def directive(self, statement: Statement) -> Optional[InstructionUnit]:
        if (e := self.__DIRECTIVES_TABLE.get(statement.lexeme)) is None:
            self.errorStatement("InvalidDirective", statement)
            return

        arg_count, func = e

        if arg_count is None or len(statement.args) == arg_count:
            return func(statement)

        self.errorStatement("InvalidArgCount", statement)

    def directiveUsePackage(self, statement: Statement):
        if self.__used_package_directive:
            self.errorStatement("PackageAlreadyUsed", statement)
            return

        self.__used_package_directive = True
        self.__env.packages.use(statement.args[0])

    def directiveUsePlatform(self, statement: Statement):
        if self.__used_platform_directive:
            self.errorStatement("PlatformAlreadyUsed", statement)
            return

        self.__used_platform_directive = True
        self.__env.platforms.use(statement.args[0])

        self.__mark_offset = self.__env.getPlatform().HEAP_PTR.size
        self.__ptr_addr_next = int(self.__mark_offset)

    def directiveDefineMacro(self, statement):
        name, value = statement.args
        self.__env.consts[name] = value

    def directiveUseInline(self, statement: Statement) -> InstructionUnit:
        lexeme, *args = statement.args
        return self.instructionFull(Statement(StatementType.INSTRUCTION, lexeme, args, statement.line, statement.source_line), True)

    def directiveInitPointer(self, statement: Statement):
        _type, name, value_lexeme = statement.args

        if (_type := PrimitiveCollection.get(_type)) is None:
            self.errorStatement("InvalidType", statement)
            return

        address = self.__ptr_addr_next

        if (address + _type.size) > self.__env.start:
            self.errorStatement("AddressAfterHeap", statement)
            return

        if name in self.__env.variables:
            self.errorStatement("RedefineVariable", statement)
            return

        value_bytes = self.__env.writeValue(value_lexeme, _type)
        value_lexeme = _type.read(value_bytes)

        if not (_type.min <= value_lexeme <= _type.max):
            self.errorStatement("ParsingErrorNotInRange[{_type.min};{_type.max}]", statement)
            return

        ret = self.__env.variables[name] = PointerVariable(name, address, _type, value_bytes)
        self.__env.addr_vars.add(address)
        self.__ptr_addr_next += ret.getSize(self.__env.getPlatform())

    def directiveSetHeap(self, statement: Statement):
        if self.__used_heap_directive:
            self.errorStatement("ReinitHeap", statement)
            return

        self.__used_heap_directive = True

        platform = self.__env.getPlatform()
        h = self.__env.start = self.__env.readConst(statement.args[0])
        self.__mark_offset += h

        if not (0 < h < platform.HEAP_PTR.max):
            self.errorStatement("InvalidHeapSize", statement)


class ProgramGenerator(ErrorHandler):
    """Компилятор в байткод"""

    def __init__(self, environment: Environment):
        super().__init__(self)
        self.environment = environment

    def run(self, statementsUnits: Iterable[InstructionUnit]) -> Optional[bytes]:
        ret = self.__getHeap() + self.__getProgram(statementsUnits)

        if (L := len(ret)) > (max_len := self.environment.getPlatform().PROGRAM_LEN):
            self.addErrorMessage(f"Program too long ({L}/{max_len})")
            return

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

        self.lexical_analyser = LexicalAnalyser(e)
        self.code_generator = CodeGenerator(e)
        self.program_generator = ProgramGenerator(e)

        self.__statements: Optional[Iterable[Statement]] = None
        self.__instructions: Optional[Iterable[InstructionUnit]] = None
        self.__program: Optional[bytes] = None

    def run(self, source: str) -> None:
        self.__statements = self.lexical_analyser.run(source)

        if self.lexical_analyser.hasErrors():
            raise ByteLangCompileError(self.lexical_analyser)

        self.__instructions = self.code_generator.run(self.__statements)
        if self.code_generator.hasErrors():
            raise ByteLangCompileError(self.code_generator)

        self.__program = self.program_generator.run(self.__instructions)
        if self.program_generator.hasErrors():
            raise ByteLangCompileError(self.program_generator)

    def getProgram(self) -> bytes:
        return self.__program

    def getInstructions(self) -> Iterable[InstructionUnit]:
        return self.__instructions

    def getStatements(self) -> Iterable[Statement]:
        return self.__statements

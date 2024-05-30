from __future__ import annotations

from typing import Iterable, Optional, Callable

from .data import Argument, PointerVariable, InstructionUnit, Platform, Package
from .errors import ByteLangCompileError
from .handlers import ErrorHandler
from .loaders import PackageLoader, PlatformLoader
from .mini import StatementType, Statement
from .primitives import PrimitiveCollection


# TODO Lexical, Syntax??
class LexicalAnalyser(ErrorHandler):

    def __init__(self):
        super().__init__(self)
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
            self.errorMessage(f"Invalid Statement: '{lexeme}'\t at Line {index}")

        return Statement(_type, lexeme, args, index, line_clean)


class CodeGenerator(ErrorHandler):
    BASES_PREFIXES: dict[str, int] = {'x': 16, 'o': 8, 'b': 2}

    def __init__(self, environment: Compiler):
        super().__init__(self)
        self.env = environment

        self.__mark_offset: Optional[int] = None
        self.__ptr_addr_next: int = 0

        self.__used_heap_directive = False
        self.__used_package_directive = False

        self.consts = dict[str, str | int]()
        """значения макро констант"""
        self.addr_vars = set[int]()
        """множество адресов существующих переменных"""

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

    def getPlatform(self) -> Platform:
        return self.env.platforms.current

    def getPackage(self) -> Package:
        return self.env.packages.current

    def run(self, statements: Iterable[Statement]) -> Iterable[InstructionUnit]:

        ret = list[InstructionUnit]()

        for statement in statements:
            if (u := self.__STATEMENT_TYPE_TABLE.get(statement.type)(statement)) is not None:
                ret.append(u)

        return ret

    def readConst(self, lexeme: str) -> Optional[int | float]:
        # лексема - имя константы -> значение константы
        if (ret := self.consts.get(lexeme)) is not None:
            return self.readConst(ret)

        # лексема - имя переменной -> адрес переменной
        if (ret := self.env.variables.get(lexeme)) is not None:
            return ret.address

        # лексема - float
        if "." in lexeme:
            try:
                return float(lexeme)

            except ValueError:
                self.errorMessage(f"'{lexeme}' is not float")
                return

        # может быть int
        base = 10

        if len(lexeme) > 2 and lexeme[0] == '0' and (base := self.BASES_PREFIXES.get(lexeme[1])) is None:
            self.errorMessage(f"IncorrectBasePrefix: {lexeme}")
            return

        try:
            return int(lexeme, base)

        except ValueError:
            self.errorMessage(f"'{lexeme}' is not int")
            return

    def mark(self, statement: Statement):
        if self.__mark_offset is None:
            self.errorStatement("MustUsePlatform", statement)
            return

        self.consts[statement.lexeme] = self.__mark_offset

    def instruction(self, statement: Statement, inline_last: bool = False) -> Optional[InstructionUnit]:
        if (p := self.getPackage()) is None:
            self.errorStatement("need to select package", statement)
            return

        instruction = p.INSTRUCTIONS.get(statement.lexeme)

        if instruction is None:
            self.errorStatement("InvalidInstruction", statement)
            return

        if instruction.can_inline is False and inline_last is True:
            self.errorStatement("CantInline", statement)
            return

        if len(instruction.signature) != len(statement.args):
            self.errorStatement("InvalidArgumentCount", statement)
            return

        if (p := self.getPlatform()) is None:
            self.errorStatement("need to select platform", statement)
            return

        self.__mark_offset += instruction.getSize(p, inline_last)

        if (args := self.instructionValidateArg(statement, instruction.signature, inline_last)) is None:
            self.errorStatement("ErrorArgs", statement)
            return

        return InstructionUnit(instruction, args, inline_last)

    def instructionValidateArg(self, statement: Statement, signature: Iterable[Argument], inline: bool) -> Optional[tuple[bytes, ...]]:
        ret = list[bytes]()

        for index, (arg_state, arg_lexeme) in enumerate(zip(signature, statement.args)):
            if (arg_value := self.readConst(arg_lexeme)) is None:
                self.errorStatement(f"Could not find value for '{arg_lexeme}'", statement)
                return

            arg_primitive = arg_state.getPrimitive(self.getPlatform())

            if not (arg_primitive.min <= arg_value <= arg_primitive.max):
                self.errorStatement(f"InvalidValue {arg_lexeme} ({arg_value}) not in [{arg_primitive.min};{arg_primitive.max}]", statement)
                return

            if not inline and arg_state.pointer and arg_value not in self.addr_vars:
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
        self.env.packages.use(statement.args[0])

    def directiveUsePlatform(self, statement: Statement):
        if self.env.platforms.current is not None:
            self.errorStatement("PlatformAlreadyUsed", statement)
            return

        self.env.platforms.use(statement.args[0])
        self.__mark_offset = self.getPlatform().HEAP_PTR.size
        self.__ptr_addr_next = int(self.__mark_offset)

    def directiveDefineMacro(self, statement):
        name, value = statement.args
        self.consts[name] = value

    def directiveUseInline(self, statement: Statement) -> InstructionUnit:
        lexeme, *args = statement.args
        return self.instruction(Statement(StatementType.INSTRUCTION, lexeme, args, statement.line, statement.source_line), True)

    def directiveInitPointer(self, statement: Statement):
        _type, name, lexeme = statement.args

        if (_type := PrimitiveCollection.get(_type)) is None:
            self.errorStatement("InvalidType", statement)
            return

        address = self.__ptr_addr_next

        if (address + _type.size) > self.env.start:
            self.errorStatement("AddressAfterHeap", statement)
            return

        if name in self.env.variables:
            self.errorStatement("RedefineVariable", statement)
            return

        p_value = self.readConst(lexeme)
        p_bytes = _type.write(p_value)

        if not (_type.min <= p_value <= _type.max):
            self.errorStatement(f"({p_value}) NotInRange[{_type.min};{_type.max}]", statement)
            return

        ret = self.env.variables[name] = PointerVariable(name, address, _type, p_bytes)
        self.addr_vars.add(address)

        if (p := self.getPlatform()) is None:
            self.errorStatement("need to select platform", statement)
            return

        self.__ptr_addr_next += ret.getSize(p)

    def directiveSetHeap(self, statement: Statement):
        if self.__used_heap_directive:
            self.errorStatement("ReinitHeap", statement)
            return

        self.__used_heap_directive = True
        h = self.env.start = self.readConst(statement.args[0])

        if (p := self.getPlatform()) is None:
            self.errorStatement("need to select platform", statement)
            return

        self.__mark_offset += h

        if not (0 < h < p.HEAP_PTR.max):
            self.errorStatement("InvalidHeapSize", statement)


class ProgramGenerator(ErrorHandler):
    """Компилятор в байткод"""

    def __init__(self, environment: Compiler):
        super().__init__(self)
        self.environment = environment

    def run(self, statementsUnits: Iterable[InstructionUnit]) -> Optional[bytes]:
        ret = self.__getHeap() + self.__getProgram(statementsUnits)

        if (L := len(ret)) > (max_len := self.environment.platforms.current.PROGRAM_LEN):
            self.errorMessage(f"Program too long ({L}/{max_len})")
            return

        return ret

    def __getProgram(self, statementsUnits: Iterable[InstructionUnit]):
        return b''.join(unit.write(self.environment.platforms.current) for unit in statementsUnits)

    def __getHeap(self):
        h_ptr = self.environment.platforms.current.HEAP_PTR
        size = self.environment.start
        heap_data = h_ptr.write(size + h_ptr.size)  # TODO wtf

        if size == 0:
            return heap_data

        heap_data = list(heap_data + bytes(size))

        for var in self.environment.variables.values():
            compiler = self.environment
            var_bytes = list(var.write(compiler.platforms.current))
            for i, b in enumerate(var_bytes):
                heap_data[i + var.address] = b

        return bytes(heap_data)


class Compiler:

    def __init__(self, packages_folder: str, platforms_folder: str):

        self.packages = PackageLoader(packages_folder)
        """Загрузчик пакетов инструкций"""
        self.platforms = PlatformLoader(platforms_folder)
        """Загрузчик платформ"""

        self.start: int = 0
        """Индекс байта начала кода"""
        self.variables = dict[str, PointerVariable]()
        """переменные"""

        self.lexical_analyser = LexicalAnalyser()
        self.code_generator = CodeGenerator(self)
        self.program_generator = ProgramGenerator(self)

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

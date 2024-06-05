from __future__ import annotations

from typing import Iterable, Optional, Callable

from .data import Argument, PointerVariable, InstructionUnit, Platform, Package
from .handlers import ErrorHandler
from .loaders import PackageLoader, PlatformLoader
from .mini import StatementType, Statement
from .primitives import PrimitiveCollection
from .tools import ReprTool


# TODO Lexical, Syntax??
class LexicalAnalyser:

    def __init__(self, error_handler: ErrorHandler):
        self.__err = error_handler
        self.COMMENT = "#"
        self.MARK = ":"
        self.DIRECTIVE = "."

    def run(self, source: str) -> Iterable[Statement]:
        ret = list()

        for index, source_line in enumerate(source.split("\n")):
            if line := source_line.split(self.COMMENT)[0].strip():
                ret.append(self.__createStatement(index + 1, line))

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
            self.__err.message(f"Invalid Statement: '{lexeme}'\t at Line {index}")

        return Statement(_type, lexeme, args, index, line_clean)


class CodeGenerator:
    BASES_PREFIXES: dict[str, int] = {'x': 16, 'o': 8, 'b': 2}

    def __init__(self, environment: Compiler):
        self.env = environment

        self.__err = environment.errors

        self.__mark_offset: Optional[int] = None
        self.__ptr_addr: int = 0

        self.__used_heap_directive = False

        self.consts = dict[str, str | int | float]()
        """значения макро констант: def, mark, var_addr"""

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

    def __reset(self) -> None:
        self.__mark_offset = None
        self.__ptr_addr = 0
        self.__used_heap_directive = False
        self.consts.clear()

    def __addConst(self, statement: Statement, name: str, value: str | int | float) -> bool:
        """
        Добавить константное значение
        :param statement: выражение
        :param name: идентификатор
        :param value: значение
        :return: True если удалось добавить, False при ошибке
        """
        if self.__checkNameExist(name):
            self.__err.nameExist(statement, name)
            return False

        self.consts[name] = value
        return True

    def getPlatform(self) -> Platform:
        return self.env.platforms.current

    def getPackage(self) -> Package:
        return self.env.packages.current

    def run(self, statements: Iterable[Statement]) -> Iterable[InstructionUnit]:
        self.__reset()
        ret = list[InstructionUnit]()

        for statement in statements:
            if (u := self.__STATEMENT_TYPE_TABLE.get(statement.type)(statement)) is not None:
                ret.append(u)

        return ret

    def readConst(self, lexeme: str) -> Optional[int | float]:
        # лексема - имя константы -> значение константы
        if (ret := self.consts.get(lexeme)) is not None:
            if isinstance(ret, (int, float)):
                return ret

            return self.readConst(ret)

        # лексема - float
        if "." in lexeme:
            try:
                return float(lexeme)

            except ValueError:
                self.__err.invalidType(lexeme, "float")
                return

        # может быть int
        base = 10

        self.__err.begin()

        if len(lexeme) > 2 and lexeme[0] == '0' and (base := self.BASES_PREFIXES.get(lexeme[1])) is None:
            self.__err.message(f"invalid integer base prefix '{lexeme[:2]}' not in {ReprTool.iter(self.BASES_PREFIXES.keys())}")

        try:
            return int(lexeme, base)

        except ValueError:
            self.__err.invalidType(lexeme, "int")

    def mark(self, statement: Statement):
        self.__err.begin()

        if self.__mark_offset is None:
            self.__err.platformNotSelected(statement)

        if not self.__err.begin():
            self.__addConst(statement, statement.lexeme, self.__mark_offset)

    def __checkNameExist(self, name: str) -> bool:
        return name in self.consts.keys() or name in self.env.variables.keys() or name in self.getPackage().INSTRUCTIONS.keys()

    def instruction(self, statement: Statement, inline_last: bool = False) -> Optional[InstructionUnit]:
        self.__err.begin()

        if (platform := self.getPlatform()) is None:
            self.__err.platformNotSelected(statement)

        if (package := self.getPackage()) is None:
            self.__err.packageNotSelected(statement)

        instruction = package.INSTRUCTIONS.get(statement.lexeme)

        if instruction is None:
            self.__err.statement("unknown instruction", statement)

        if self.__err.begin():
            return

        if instruction.can_inline is False and inline_last is True:
            self.__err.statement("Instruction cannot inlined", statement)

        if (need := len(instruction.signature)) != len(statement.args):
            self.__err.invalidArgCount(statement, need)

        if (args := self.instructionValidateArg(statement, instruction.signature, inline_last)) is None:
            self.__err.statement("args err", statement)

        if self.__err.begin():
            return

        self.__mark_offset += instruction.getSize(platform, inline_last)
        return InstructionUnit(instruction, args, inline_last)

    def instructionValidateArg(self, statement: Statement, signature: Iterable[Argument], inline: bool) -> Optional[tuple[bytes, ...]]:
        ret = list[bytes]()

        for index, (arg_state, arg_lexeme) in enumerate(zip(signature, statement.args)):
            if (arg_value := self.readConst(arg_lexeme)) is None:
                self.__err.unknownName(arg_lexeme, statement)
                return

            arg_primitive = arg_state.getPrimitive(self.getPlatform(), inline)

            if not (arg_primitive.min <= arg_value <= arg_primitive.max):
                self.__err.statement(f"InvalidValue {arg_lexeme} ({arg_value}) not in [{arg_primitive.min};{arg_primitive.max}]", statement)
                return

            # if not inline and arg_state.pointer and arg_value not in self.env.variables.keys():
            #     self.__err.statement(f"count not find variable at {arg_value}", statement)
            #     return

            ret.append(arg_primitive.write(arg_value))

        return tuple(ret)

    def directive(self, statement: Statement) -> Optional[InstructionUnit]:
        if (e := self.__DIRECTIVES_TABLE.get(statement.lexeme)) is None:
            self.__err.statement("InvalidDirective", statement)
            return

        arg_count, func = e

        if arg_count is None or len(statement.args) == arg_count:
            return func(statement)

        self.__err.invalidArgCount(statement, arg_count)

    def directiveUsePackage(self, statement: Statement):
        if self.getPackage() is not None:
            self.__err.statement("PackageAlreadyUsed", statement)
            return

        self.env.packages.use(statement.args[0])  # TODO name check

    def directiveUsePlatform(self, statement: Statement):
        if self.env.platforms.current is not None:
            self.__err.statement("PlatformAlreadyUsed", statement)
            return

        self.env.platforms.use(statement.args[0])  # TODO name check
        self.__mark_offset = self.getPlatform().HEAP_PTR.size
        self.__ptr_addr = int(self.__mark_offset)

    def directiveDefineMacro(self, statement):
        name, value = statement.args
        self.__addConst(statement, name, value)

    def directiveUseInline(self, statement: Statement) -> Optional[InstructionUnit]:
        if not statement.args:
            self.__err.statement("inline must have next instruction", statement)

        lexeme, *args = statement.args
        return self.instruction(Statement(StatementType.INSTRUCTION, lexeme, args, statement.line, statement.source_line), True)

    def directiveInitPointer(self, statement: Statement):
        self.__err.begin()

        if (p := self.getPlatform()) is None:
            self.__err.platformNotSelected(statement)

        _type, name, lexeme = statement.args

        if self.__checkNameExist(name):
            self.__err.nameExist(statement, name)

        if (_type := PrimitiveCollection.get(_type)) is None:
            self.__err.statement("InvalidType", statement)

        if self.__err.begin():
            return

        if (self.__ptr_addr + _type.size) > self.env.start:
            self.__err.statement("AddressAfterHeap", statement)

        if (p_value := self.readConst(lexeme)) is None:
            self.__err.statement("unknown value", statement)

        if self.__err.begin():
            return

        if not (_type.min <= p_value <= _type.max):
            self.__err.statement(f"({p_value}) NotInRange[{_type.min};{_type.max}]", statement)
            return

        if self.__addConst(statement, name, self.__ptr_addr):
            ret = self.env.variables[self.__ptr_addr] = PointerVariable(name, self.__ptr_addr, _type, _type.write(p_value))
            self.__ptr_addr += ret.getSize(p)

    def directiveSetHeap(self, statement: Statement):
        if (p := self.getPlatform()) is None:
            self.__err.platformNotSelected(statement)

        if self.__used_heap_directive:
            self.__err.statement("ReinitHeap", statement)

        self.__used_heap_directive = True
        h = self.env.start = self.readConst(statement.args[0])

        if not (0 < h < p.HEAP_PTR.max):
            self.__err.statement("InvalidHeapSize", statement)


class ProgramGenerator:
    """Компилятор в байткод"""

    def __init__(self, environment: Compiler):
        self.environment = environment
        self.__err = environment.errors

    def run(self, statementsUnits: Iterable[InstructionUnit]) -> Optional[bytes]:
        ret = self.__getHeap() + self.__getProgram(statementsUnits)

        if (L := len(ret)) > (max_len := self.environment.platforms.current.PROGRAM_LEN):
            self.__err.message(f"Program too long ({L}/{max_len})")
            return

        return ret

    def __getProgram(self, statementsUnits: Iterable[InstructionUnit]):
        return b''.join(unit.write(self.environment.platforms.current) for unit in statementsUnits)

    def __getHeap(self):
        h_ptr = self.environment.platforms.current.HEAP_PTR
        size = self.environment.start
        heap_data = h_ptr.write(size + h_ptr.size)

        if size == 0:
            return heap_data

        heap_data = list(heap_data + bytes(size))

        for var in self.environment.variables.values():
            var_bytes = list(var.write(self.environment.platforms.current))
            for i, b in enumerate(var_bytes):
                heap_data[i + var.address] = b

        return bytes(heap_data)


class Compiler:

    def __init__(self, packages_folder: str, platforms_folder: str):
        self.errors = ErrorHandler(self)

        self.packages = PackageLoader(packages_folder)
        """Загрузчик пакетов инструкций"""
        self.platforms = PlatformLoader(platforms_folder)
        """Загрузчик платформ"""

        self.start: int = 0
        """Индекс байта начала кода"""
        self.variables = dict[int, PointerVariable]()
        """переменные: индекс - данные"""

        self.lexical_analyser = LexicalAnalyser(self.errors)
        self.code_generator = CodeGenerator(self)
        self.program_generator = ProgramGenerator(self)

        self.__statements: Optional[Iterable[Statement]] = None
        self.__instructions: Optional[Iterable[InstructionUnit]] = None
        self.__program: Optional[bytes] = None

    def __reset(self):
        self.errors.reset()
        self.start = 0
        self.variables.clear()
        self.__statements = None
        self.__instructions = None
        self.__program = None
        self.packages.current = None
        self.platforms.current = None

    def run(self, source: str) -> None:
        self.__reset()

        self.__statements = self.lexical_analyser.run(source)
        if self.errors.has():
            return

        self.__instructions = self.code_generator.run(self.__statements)
        if self.errors.has():
            return

        self.__program = self.program_generator.run(self.__instructions)
        if self.errors.has():
            return

    def getCompileLog(
            self, *,
            instructions: bool = False,
            statements: bool = False,
            code: bool = False,
            constants: bool = False,
            variables: bool = False,
            program: bool = False,
            sizes: bool = False
    ) -> str:
        m = list[tuple[str, Iterable]]()

        if sizes:
            m.append(("size", (f"program: {len(self.__program)}",)))

        if instructions:
            m.append(("instructions package", self.packages.current.INSTRUCTIONS.values()))

        if statements:
            m.append(("statements", self.getStatements()))

        if code:
            m.append(("instructions program compiled", self.getInstructions()))

        if constants:
            m.append(("constants", self.code_generator.consts.items()))

        if variables:
            m.append(("variables", self.variables.values()))

        if program:
            m.append(("program", (f"{byte:02X}" for byte in self.getProgram())))

        return "\n".join((ReprTool.headed(header, items) for header, items in m))

    def getProgram(self) -> bytes:
        return self.__program

    def getInstructions(self) -> Iterable[InstructionUnit]:
        return self.__instructions

    def getStatements(self) -> Iterable[Statement]:
        return self.__statements

from typing import Iterable, Optional, Callable

from . import primitives
from .data import Package, Platform, Argument, PointerVariable, InstructionUnit
from .errors import ByteLangError, LexicalError, CodeGenerationError, CompileError
from .loaders import PackageLoader, PlatformLoader
from .mini import StatementType, Statement, DirectiveUnit, DirectivesCollection, CharSettings, ProgramData


class Environment:

    def __init__(self, packages: PackageLoader, platforms: PlatformLoader):
        self.packages = packages
        self.platforms = platforms

        self.program = ProgramData()
        self.CHAR = CharSettings('#', ':', '.')
        self.DIRECTIVE = DirectivesCollection(
            SET_HEAP=DirectiveUnit("heap", 1),
            INIT_POINTER=DirectiveUnit("ptr", 3),
            USE_INLINE=DirectiveUnit("inline", None),
            DEFINE_MACRO=DirectiveUnit("def", 2),
            USE_PACKAGE=DirectiveUnit("package", 1),
            USE_PLATFORM=DirectiveUnit("platform", 1)
        )

    def getPlatform(self) -> Platform:
        return self.platforms.get()

    def getPackage(self) -> Package:
        return self.packages.get()

    def parsingError(self, message: str, statement: Statement) -> None:
        raise CodeGenerationError(f"[ parse error ] :: {message} : {statement}")


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
        self.environment = environment

        self.mark_offset: int = 0
        self.ptr_addr_next: int = 0

        self.used_heap_directive = False
        self.used_package_directive = False
        self.used_platform_directive = False

        d = self.environment.DIRECTIVE

        self.DIRECTIVES: dict[str, DirectiveUnit] = {
            directive.name: directive
            for directive in self.environment.DIRECTIVE.__dict__.values()
        }

        self.DIRECTIVE_CALLBACKS: dict[DirectiveUnit, Callable[[Statement], None | InstructionUnit]] = {
            d.SET_HEAP: self.directiveSetHeap,
            d.DEFINE_MACRO: self.directiveDefineMacro,
            d.INIT_POINTER: self.directiveInitPointer,
            d.USE_INLINE: self.directiveUseInline,
            d.USE_PACKAGE: self.directiveUsePackage,
            d.USE_PLATFORM: self.directiveUsePlatform
        }

    def run(self, statements: Iterable[Statement]) -> Iterable[InstructionUnit]:
        self.mark_offset = 0

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
        if not self.used_platform_directive:
            self.environment.parsingError("MustUsePlatform", statement)

        self.environment.program.constants[statement.lexeme] = self.mark_offset

    def getValue(self, arg_lexeme: str) -> int:
        """Получить значение из лексемы"""

        if isinstance(arg_lexeme, int):
            return arg_lexeme

        # данное значение найдено среди констант
        if (val := self.environment.program.constants.get(arg_lexeme)) is not None:
            return self.getValue(val)

        # если указатель - возвращаем адрес
        if (val := self.environment.program.variables.get(arg_lexeme)) is not None:
            return val.ptr

        # ничего не было найдено, возможно это число

        base = 10

        if len(arg_lexeme) > 2 and arg_lexeme[0] == '0' and (base := self.BASES_PREFIXES.get(arg_lexeme[1])) is None:
            raise CodeGenerationError(f"IncorrectBasePrefix: {arg_lexeme}")

        try:
            return int(arg_lexeme, base)

        except ValueError as e:
            raise CodeGenerationError(f"NotValid value '{arg_lexeme}' error: {e}")

    def instruction(self, statement: Statement, inline_last: bool = False) -> InstructionUnit:
        instruction = self.environment.getPackage().INSTRUCTIONS.get(statement.lexeme)

        if instruction is None:
            self.environment.parsingError("InvalidInstruction", statement)

        if instruction.can_inline is False and inline_last is True:
            self.environment.parsingError("CantInline", statement)

        if len(instruction.signature) != len(statement.args):
            self.environment.parsingError("InvalidArgument", statement)

        self.mark_offset += instruction.getSize(self.environment.getPlatform(), inline_last)

        return InstructionUnit(instruction, self.instructionValidateArg(statement, instruction.signature, inline_last), inline_last)

    def instructionValidateArg(self, statement: Statement, signature: tuple[Argument, ...], inline: bool) -> tuple[int, ...]:
        ret = list[int]()

        for index, (arg_type, arg_value) in enumerate(zip(signature, statement.args)):
            arg_value = self.getValue(arg_value)
            if not inline and arg_type.pointer and arg_value not in self.environment.program.addr_vars.keys():
                self.environment.parsingError("AddrError", statement)

            ret.append(arg_value)

        return tuple(ret)

    def directive(self, statement: Statement) -> InstructionUnit | None:
        if (d := self.DIRECTIVES.get(statement.lexeme)) is None:
            self.environment.parsingError("InvalidDirective", statement)

        if d.arg_count is not None and len(statement.args) != d.arg_count:
            raise self.environment.parsingError("InvalidArgCount", statement)

        return self.DIRECTIVE_CALLBACKS.get(d)(statement)

    def directiveUsePackage(self, statement: Statement):
        if self.used_package_directive:
            self.environment.parsingError("PackageAlreadyUsed", statement)

        self.used_package_directive = True
        self.environment.packages.use(statement.args[0])

    def directiveUsePlatform(self, statement: Statement):
        if self.used_platform_directive:
            self.environment.parsingError("PlatformAlreadyUsed", statement)

        self.used_platform_directive = True
        self.environment.platforms.use(statement.args[0])

        self.mark_offset = self.environment.getPlatform().HEAP_PTR.size
        self.ptr_addr_next = int(self.mark_offset)

    def directiveDefineMacro(self, statement):
        name, value = statement.arg_count
        self.environment.program.constants[name] = self.getValue(value)

    def directiveUseInline(self, statement: Statement) -> InstructionUnit:
        lexeme, *args = statement.args
        return self.instruction(Statement(StatementType.INSTRUCTION, lexeme, args, statement.line, statement.source_line), True)

    def directiveInitPointer(self, statement: Statement):
        ptr_type, ptr_name, ptr_value = statement.args

        if (ptr_type := primitives.Collection.get(ptr_type)) is None:
            self.environment.parsingError("InvalidType", statement)

        ptr_addr = self.ptr_addr_next

        if ptr_addr < self.environment.getPlatform().HEAP_PTR.size:
            self.environment.parsingError("AddressBeforeHeap", statement)

        if (ptr_addr + ptr_type.size) > self.environment.program.heap_size:
            self.environment.parsingError("AddressAfterHeap", statement)

        p_vars = self.environment.program.variables

        if ptr_name in p_vars:
            self.environment.parsingError("RedefineVariable", statement)

        if not (ptr_type.min <= (ptr_value := self.getValue(ptr_value)) <= ptr_type.max):
            raise self.environment.parsingError(f"NotInRange[{ptr_type.min};{ptr_type.max}]", statement)

        ret = p_vars[ptr_name] = PointerVariable(ptr_name, ptr_addr, ptr_type, ptr_value)
        self.environment.program.addr_vars[ptr_addr] = ret
        self.ptr_addr_next += ret.getSize(self.environment.getPlatform())

    def directiveSetHeap(self, statement: Statement):
        if self.used_heap_directive:
            self.environment.parsingError("ReinitHeap", statement)

        self.used_heap_directive = True
        h = self.environment.program.heap_size = self.getValue(statement.args[0])
        self.mark_offset += h

        if not (0 < h < self.environment.getPlatform().HEAP_PTR.max):
            self.environment.parsingError("InvalidHeapSize", statement)


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
        ptr_size = self.environment.getPlatform().HEAP_PTR.size
        size = self.environment.program.heap_size
        heap_data = primitives.Collection.pointer(ptr_size).toBytes(size + ptr_size)

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

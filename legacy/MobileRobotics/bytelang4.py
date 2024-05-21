import typing

import typez
import utils


class DirectiveUnit(utils.File.JsonUnpacker):

    def __init__(self, data: typez.Json):
        self.name: str | None = None
        self.args: int | None = None

        super().__init__(data)

        arg_str = "..." if self.args is None else (", ".join(["___"] * self.args))
        self.__string = f"{self.name} {arg_str}"

    def __repr__(self):
        return self.__string


class Directives(utils.File.JsonUnpacker):

    @staticmethod
    def __parseDirectivesDict(data: typez.Json) -> typez.StringDict:
        return {unit["name"]: name for name, unit in data.items()}

    def __init__(self, data: typez.Json):
        self.DEFINE_MACRO: DirectiveUnit | None = None
        self.PROGRAM_START: DirectiveUnit | None = None
        self.INLINE_ARG: DirectiveUnit | None = None
        self.STATIC_SET: DirectiveUnit | None = None
        self.DEFINE_VAR: DirectiveUnit | None = None

        super().__init__(data, DirectiveUnit)

        self.__directives_dict = self.__parseDirectivesDict(data)
        self.__directives_loaded = [ self.get(key) for key in self.__directives_dict.keys() ]

    def getLoaded(self) -> list[DirectiveUnit]:
        return self.__directives_loaded

    def exist(self, directive: typez.Name) -> bool:
        return directive in self.__directives_dict.keys()

    def getAvailable(self) -> typez.StringSet:
        return typez.StringSet(self.__directives_dict.keys())

    def get(self, name: typez.Name) -> DirectiveUnit:
        return self.__dict__[self.__directives_dict[name]]


class CommandUnit(utils.File.JsonUnpacker):
    """
    Команда ByteLang
    """

    SIGNATURES: dict[str, typez.StringList] | None = None

    INLINE_BIT = 0b10000000

    word_min: int = None
    word_max: int = None
    word_type: typez.Bytes.Format = None

    @classmethod
    def init(cls, types: dict[str, typez.StringList]):

        for items in types.values():
            for item in items:
                if not utils.Bytes.typeExist(item):
                    raise TypeError(f"Invalid type '{item}'")

        cls.SIGNATURES = types
        cls.word_type = cls.SIGNATURES["word"][0]
        cls.word_min, cls.word_max = utils.Bytes.getRange(cls.word_type)

    def __init__(self, identifier: typez.Name, index: int, package: typez.Path, data: typez.Json):
        self.identifier = identifier
        self.index = index
        self.package = package.split("/")[-1].split(".")[0]

        self.signature: None | str = None
        self.description = None
        self.inlining = True
        self.tested = False

        super().__init__(data)

        self.arguments = self.SIGNATURES[self.signature]
        self.size = utils.Bytes.sizeof(self.arguments) + 1
        self.arg_count = len(self.arguments)
        self.__string = f"{self.package}.{self.identifier}:{self.index}({self.signature})"

    def __repr__(self):
        return self.__string


class ProgramVariable:
    """
    Переменная программы
    """

    def __init__(self, identifier: typez.Name, index: int, line: int):
        self.identifier = identifier
        self.index = index
        self.usage = 0
        self.declaration_line = line

    def __repr__(self):
        return f"<var at {self.index} '{self.identifier}'>"


class ByteLangBaseError(Exception):
    """
    Базовая ошибка ByteLang
    """

    def __init__(self, message: str):
        super().__init__(f"[ BYTELANG ERROR ]\n{message}")


class ByteLangProgramError(ByteLangBaseError):
    """
    Ошибка при построении программы
    """


class ByteLangCompilationError(ByteLangBaseError):
    """
    Ошибка компиляции
    """


class CompilerEnvironment:

    @staticmethod
    def __getSettingsItems(prefixes: typez.StringDict, keys: typez.StringList, name_modify_func=lambda x: x) -> typez.StringList:
        return [name_modify_func(prefixes[key]) for key in keys]

    def __init__(
            self,
            bytelang_compiler_dir: typez.Path,
            settings_file: typez.Path,
            command_packages: typez.StringList):
        # КОНСТАНТЫ КОМПИЛЯТОРА

        self.COMPILER_DIR = bytelang_compiler_dir
        self.SETTINGS_FILE = self.__homePath(settings_file)

        settings_json = utils.File.readJSON(self.SETTINGS_FILE)

        self.COMMAND_PACKAGES_DIR = self.__homePath(settings_json["command_packages_dir"])
        self.COMMAND_PACKAGES_USE = command_packages
        self.COMMAND_SIGNATURES = settings_json["types"]
        CommandUnit.init(self.COMMAND_SIGNATURES)
        self.COMMANDS = self.__loadCommandPackages()

        self.DIRECTIVES_FILE = self.__homePath(settings_json["directives"])
        self.DIRECTIVES = Directives(utils.File.readJSON(self.DIRECTIVES_FILE))

        self.MAX_PROGRAM_MEMORY = settings_json["memory"]
        self.MAX_HEAP_SIZE = settings_json["heap"]

        (self.CHAR_DIRECTIVE, self.CHAR_COMMENT) = self.__getSettingsItems(settings_json["syntax"], ["directive", "comment"])
        (self.PREFIX_VAR, self.PREFIX_MACRO, self.PREFIX_MARK) = self.__getSettingsItems(settings_json["prefix"], ["variable", "macro", "mark"], lambda x: f"{x}_")

        # ПЕРЕМЕННЫЕ КОМПИЛЯТОРА

        self.heap_data: typez.IntList | None = None
        self.variables = dict[typez.Name, ProgramVariable]()
        self.macro_constants = typez.IntDict()

        self.source_file: str | None = None
        self.output_file: str | None = None
        self.line_index: int | None = None
        self.code_line: str | None = None
        self.arg_count: int | None = None
        self.heap_index: int | None = None
        self.program_size: int | None = None

    def __homePath(self, file: typez.Path) -> typez.Path:
        return self.COMPILER_DIR + file

    def __loadCommandPackages(self) -> dict[str, CommandUnit]:
        commands = dict[typez.Name, CommandUnit]()
        last_index: int = 0
        
        for package_file in self.COMMAND_PACKAGES_USE:
            package_json = utils.File.readJSON(self.COMMAND_PACKAGES_DIR + package_file)
            
            package_commands = dict()
            
            for index, (name, data) in enumerate(package_json.items()):
                package_commands[name] = CommandUnit(name, index + last_index, package_file, data)
            
            last_index += index + 1
            
            commands.update(package_commands)

        return commands

    def setFiles(self, source: typez.Path, output: typez.Path):
        self.source_file = source
        self.output_file = output

    def setLine(self, args: typez.StringList, index: int):
        self.code_line = ' '.join(args)
        self.arg_count = len(args)
        self.line_index = index


class CompileHandler:
    """
    Объект использует среду компилятора
    """

    def __init__(self, environment: CompilerEnvironment):
        self._environment = environment


class ErrorHandler(CompileHandler):
    """
    Возвращает ошибки в текущим контекстом компилятора
    """

    @staticmethod
    def __wrapMessage(message: str | None, wrap: str) -> str:
        return "" if message is None else f"\t{wrap}: {message}\n"

    @classmethod
    def __getNoteSolution(cls, solution: str, note: str) -> str:
        return cls.__wrapMessage(solution, "possible solution") + cls.__wrapMessage(note, "note")

    def __init__(self, environment: CompilerEnvironment):
        super().__init__(environment)

    def __programErrorBase(self, error: typez.Name, message: str, *, solution: str = None, note: str = None) -> ByteLangProgramError:
        return ByteLangProgramError(f"File: {self._environment.source_file} - ProgramError: {error}\n{message}\n{self.__getNoteSolution(solution, note)}")

    def programOutOfMemory(self) -> ByteLangProgramError:
        return self.__programErrorBase("ProgramOutOfMemory", f"program size: {self._environment.program_size} out of available memory: {self._environment.MAX_PROGRAM_MEMORY}")

    def __compileErrorBase(self, error: typez.Name, message: str, *, solution: str = None, note: str = None) -> ByteLangCompilationError:
        return ByteLangCompilationError(
            f"[CompileError]\nFile: {self._environment.source_file}, line: {self._environment.line_index}\n"
            f"\t{self._environment.code_line} <-- [{error}] - {message}\n"
            f"{self.__getNoteSolution(solution, note)}")

    def __compileNameError(self, message, solution: str = None, note: str = None) -> ByteLangCompilationError:
        return self.__compileErrorBase("NameError", message, solution=solution, note=note)

    def variableNotExist(self, name: typez.Name) -> ByteLangCompilationError:
        return self.__compileNameError(f"variable '{name}' not exist", f"use {self._environment.DIRECTIVES.DEFINE_VAR} to declare variable")

    def __nameRedefinitionError(self, name: typez.Name, identifier_type: str) -> ByteLangCompilationError:
        return self.__compileNameError(f"{identifier_type} name {name} already used", f"rename {identifier_type}'{name}'")

    def variableRedefinition(self, name: typez.Name) -> ByteLangCompilationError:
        return self.__nameRedefinitionError(name, "variable")

    def markRedefinition(self, name: typez.Name) -> ByteLangCompilationError:
        return self.__nameRedefinitionError(name, "mark")

    def __unknownName(self, identifier_type: str, name: typez.Name, note: str) -> ByteLangCompilationError:
        return self.__compileNameError(
            f"{identifier_type} '{name}' not exist",
            solution=f"{identifier_type}: check the existence of",
            note=note)

    def unknownCommand(self, command: typez.Name) -> ByteLangCompilationError:
        return self.__unknownName("command", command, f"used command packages:\n{self._environment.COMMAND_PACKAGES_USE}")

    def unknownDirective(self, directive: typez.Name) -> ByteLangCompilationError:
        return self.__unknownName("directive", directive, f"directives file: {self._environment.DIRECTIVES_FILE}")

    def __compileValueError(self, message, solution: str = None, note: str = None) -> ByteLangCompilationError:
        return self.__compileErrorBase("ValueError", message, solution=solution, note=note)

    def valueOutOfRange(self, value: int) -> ByteLangCompilationError:
        return self.__compileValueError(
            f"{value}: {CommandUnit.word_type} out of range ({CommandUnit.word_min}..{CommandUnit.word_max})",
            f"try set value in {CommandUnit.word_type} range")

    def pointerOverHeap(self, pointer: int) -> ByteLangCompilationError:
        return self.__compileValueError(
            f"pointer({pointer}) over heap({self._environment.MAX_HEAP_SIZE})",
            f"use {self._environment.DIRECTIVES.PROGRAM_START} to allocate more heap memory")

    def invalidNumber(self, value) -> ByteLangCompilationError:
        return self.__compileValueError(f"value {value} is not a macro or mark or variable or number")

    def __compileArgumentError(self, message, solution: str = None, note: str = None) -> ByteLangCompilationError:
        return self.__compileErrorBase("ArgumentError", message, solution=solution, note=note)

    def invalidMacroValue(self, value) -> ByteLangCompilationError:
        return self.__compileArgumentError(f"change '{value}' value", note="macro value can't be name of a command, a mark, or a variable")

    def __invalidArgumentCount(self, handler_name: str, name: typez.Name, expected_count: int) -> ByteLangCompilationError:
        return self.__compileArgumentError(f"{handler_name} {name} has {expected_count} arguments, get {self._environment.arg_count - 1}")

    def invalidCommandArgumentCount(self, command: CommandUnit) -> ByteLangCompilationError:
        return self.__invalidArgumentCount("command", str(command), command.arg_count)

    def invalidDirectiveArgumentCount(self, directive: DirectiveUnit) -> ByteLangCompilationError:
        return self.__invalidArgumentCount("directive", str(directive), directive.args)

    def commandArgumentCantInlined(self) -> ByteLangCompilationError:
        return self.__compileArgumentError("argument can not be inlined")

    def __compileInitializationError(self, message: str, solution: str = None, note: str = None) -> ByteLangCompilationError:
        return self.__compileErrorBase("InitializationError", message, solution=solution, note=note)

    def heapNotInitialized(self) -> ByteLangCompilationError:
        return self.__compileInitializationError("need init a heap", f"use {self._environment.DIRECTIVES.PROGRAM_START} to init a heap memory")

    def heapAlreadyInitialized(self) -> ByteLangCompilationError:
        return self.__compileInitializationError("heap must be initialized once", f"remove the redundant call {self._environment.DIRECTIVES.PROGRAM_START} directive")

    def invalidHeapSize(self, size) -> ByteLangCompilationError:
        return self.__compileInitializationError(f"heap size ({size}) must be between 1..{self._environment.MAX_HEAP_SIZE}")


class WarningHandler(CompileHandler):

    def __init__(self, environment: CompilerEnvironment):
        super().__init__(environment)
        self.__warnings = typez.StringList()

    def getLog(self) -> str:
        buffer = ""
        buffer += utils.String.fromList(self.__warnings, indent=2)
        buffer += f"Total Warnings: {len(self.__warnings)}\n"

        return buffer

    def append(self, message: str):
        self.__warnings.append(f"Warning: {message}")

    def appendAtLineIndex(self, message: str, line: int = None):
        if line is None:
            line = self._environment.line_index

        self.append(f"line {line}: {message}")

    def appendLine(self, message: str):
        self.appendAtLineIndex(f"{self._environment.code_line} - {message}")

    def shouldHavePrefix(self, identifier_type: str, name: typez.Name, prefix: str):
        self.appendLine(f"{identifier_type} identifier '{name}' should be named '{prefix + name}' ")

    def variableNotUsed(self, variable: ProgramVariable):
        self.appendAtLineIndex(f"variable not used: {variable.identifier}", variable.declaration_line)

    def variableAlreadyStaticInit(self, name: typez.Name):
        self.appendLine(f"variable '{name}' already was static initialized")

    def untestedCommand(self, command: CommandUnit):
        self.appendLine(f"from '{command.package}' commands package, used untested '{command.identifier}'  ")


class CompileProcessor(CompileHandler):
    """
    Объект использует сразу компилятора
    обработчик ошибок и предупреждений
    """

    def __init__(self, environment: CompilerEnvironment, error_handler: ErrorHandler, warning_handler: WarningHandler):
        super().__init__(environment)

        self._error = error_handler
        self._warning = warning_handler

    def _readMacroOrValue(self, value: str) -> int:
        if value in self._environment.macro_constants.keys():
            value = self._environment.macro_constants[value]

        if value in self._environment.variables.keys():
            return self._environment.variables[value].index

        try:
            value = int(value)

            if not (CommandUnit.word_min <= value <= CommandUnit.word_max):
                raise self._error.valueOutOfRange(value)

            return value

        except ValueError:
            raise self._error.invalidNumber(value)


class Tokenizer(CompileHandler):

    def run(self, source_code: str) -> list[tuple[int, typez.StringList]]:
        buffer = list()
        source_lines = source_code.split("\n")

        for index, line in enumerate(source_lines):
            if (line_no_comment := line.split(self._environment.CHAR_COMMENT)[0].strip()) != "":
                buffer.append((index + 1, line_no_comment.split()))

        return buffer


class Parser(CompileProcessor):

    def __init__(self, environment: CompilerEnvironment, error_handler: ErrorHandler, warning_handler: WarningHandler):

        super().__init__(environment, error_handler, warning_handler)

        self.__PARSE_DIRECTIVE_METHOD_TABLE: dict[str, typing.Callable[[typez.StringList], None]] = {
            self._environment.DIRECTIVES.DEFINE_MACRO.name: self.__parseDirectiveMacro,
            self._environment.DIRECTIVES.PROGRAM_START.name: self.__parseDirectiveStart,
            self._environment.DIRECTIVES.DEFINE_VAR.name: self.__parseDirectiveVar,
            self._environment.DIRECTIVES.STATIC_SET.name: self.__parseDirectiveSet,
            self._environment.DIRECTIVES.INLINE_ARG.name: self.__parseDirectiveInline
        }

        self.__mark_index: int | None = None
        self.__program_start: int | None = None

        self.__set_indices = typez.IntSet()
        self.__command_queue = list[tuple[int, typez.Name, typez.StringList, bool]]()

    def __checkIdentifierPrefix(self, identifier_type: str, name: typez.Name, prefix: str):
        if not name.startswith(prefix):
            self._warning.shouldHavePrefix(identifier_type, name, prefix)

    def __setValueInHeap(self, value: int, index: int):
        data = utils.Bytes.pack([(CommandUnit.word_type, value)])

        for i, byte in enumerate(data):
            self._environment.heap_data[i + index] = byte

    def run(self, commands: list[tuple[int, typez.StringList]]):
        for line_index, line_args in commands:
            name, *args = line_args
            self._environment.setLine(line_args, line_index)

            if name[0] == self._environment.CHAR_DIRECTIVE:
                self.__parseDirective(name[1:], args)

            elif name[-1] == ':':
                self.__parseMark(name[:-1])

            elif name in self._environment.COMMANDS.keys():
                self.__parseCommand(name, args, False)

            else:
                raise self._error.unknownCommand(name)

        return self.__command_queue

    def __parseDirective(self, name: typez.Name, args: typez.StringList):
        if (directive_processor := self.__PARSE_DIRECTIVE_METHOD_TABLE.get(name)) is None:
            raise self._error.unknownDirective(name)

        directive = self._environment.DIRECTIVES.get(name)

        if (directive.args is not None) and (len(args) != directive.args):
            raise self._error.invalidDirectiveArgumentCount(directive)

        directive_processor(args)

    def __parseDirectiveInline(self, args: typez.StringList):
        command, *args = args
        self.__parseCommand(command, args, True)

    def __parseDirectiveSet(self, args: typez.StringList):
        name, value = args

        if name not in self._environment.variables.keys():
            raise self._error.variableNotExist(name)

        if (index := self._environment.variables[name].index) in self.__set_indices:
            self._warning.variableAlreadyStaticInit(name)

        self.__set_indices.add(index)
        self.__setValueInHeap(self._readMacroOrValue(value), index)

    def __parseDirectiveVar(self, args: typez.StringList):
        name, index = args
        index = int(index)

        if self.__program_start is None:
            raise self._error.heapNotInitialized()

        if name in self._environment.variables.keys():
            raise self._error.variableRedefinition(name)

        if not utils.Math.inRange(index, 1, self.__program_start - 2):
            raise self._error.pointerOverHeap(index)

        self.__checkIdentifierPrefix("variable", name, self._environment.PREFIX_VAR)
        self._environment.variables[name] = ProgramVariable(name, index, self._environment.line_index)

    def __parseDirectiveStart(self, args: typez.StringList):
        if self.__program_start is not None:
            raise self._error.heapAlreadyInitialized()

        begin_index = int(args[0])

        self._environment.heap_index = begin_index

        if not utils.Math.inRange(begin_index, 1, self._environment.MAX_HEAP_SIZE - 1):
            raise self._error.invalidHeapSize(begin_index)

        self._environment.heap_data = [0] * begin_index
        self._environment.heap_data[0] = self.__mark_index = self.__program_start = begin_index

    def __parseDirectiveMacro(self, args: typez.StringList):
        name, value = args

        if value in self._environment.COMMANDS.keys():
            raise self._error.invalidMacroValue(value)

        self.__checkIdentifierPrefix("macro", name, self._environment.PREFIX_MACRO)
        self._environment.macro_constants[name] = value

    def __parseCommand(self, name: typez.Name, args: typez.StringList, inlining: bool):
        command = self._environment.COMMANDS[name]

        if not command.inlining and inlining:
            raise self._error.commandArgumentCantInlined()

        if command.arg_count != len(args):
            raise self._error.invalidCommandArgumentCount(command)

        if not command.tested:
            self._warning.untestedCommand(command)

        self.__mark_index += command.size
        self.__command_queue.append((self._environment.line_index, name, args, inlining))

    def __parseMark(self, mark: typez.Name):
        if self.__mark_index is None:
            raise self._error.heapNotInitialized()

        if mark in self._environment.macro_constants.keys():
            raise self._error.markRedefinition(mark)

        self.__checkIdentifierPrefix("mark", mark, self._environment.PREFIX_MARK)
        self._environment.macro_constants[mark] = self.__mark_index


class Translator(CompileProcessor):

    def run(self, command_queue: list[tuple[int, typez.Name, typez.StringList, bool]]) -> typez.CompiledProgram:
        program_buffer = bytes()

        for line_index, command_name, args, inlining in command_queue:
            self._environment.setLine([command_name] + args, line_index)
            command = self._environment.COMMANDS[command_name]

            cmd_index = (inlining * CommandUnit.INLINE_BIT) | command.index

            program_buffer += bytes([cmd_index])

            if command.signature == "void":
                continue

            elif command.signature == "word":
                cmd_word = self._readMacroOrValue(args[0])

                program_buffer += utils.Bytes.pack(list(zip(command.arguments, [cmd_word])))

            elif command.signature.startswith("byte_"):

                var_indices = typez.IntList()

                last = None

                if inlining:
                    *args, last = args

                for var_name in args:
                    if (variable := self._environment.variables.get(var_name)) is None:
                        raise self._error.variableNotExist(var_name)

                    variable.usage += 1

                    var_indices.append(variable.index)

                fmt_types = list(command.arguments)

                if inlining:
                    var_indices.append(self._readMacroOrValue(last))
                    fmt_types[-1] = CommandUnit.word_type

                fmt_vals = list(zip(fmt_types, var_indices))

                program_buffer += utils.Bytes.pack(fmt_vals)

        self.__checkWarningVariableUsage()

        buffer = bytes(self._environment.heap_data) + program_buffer

        self._environment.program_size = len(program_buffer)

        if self._environment.program_size > self._environment.MAX_PROGRAM_MEMORY:
            raise self._error.programOutOfMemory()

        return buffer

    def __checkWarningVariableUsage(self):
        for variable in self._environment.variables.values():
            if variable.usage == 0:
                self._warning.variableNotUsed(variable)


class Compiler:
    """
    Компилятор ByteLang
    """

    __VERSION_MAJOR = 4
    __VERSION_MINOR = 0
    __VERSION_PATCH = 6

    def __init__(self, bytelang_compiler_dir: typez.Path, settings_file: typez.Path, command_packages: typez.StringList):
        """
        @param bytelang_compiler_dir: Корневая папка компилятора
        @param settings_file: JSON файл настроек
        @param command_packages: используемые пакеты команд
        """

        self.__environment = CompilerEnvironment(bytelang_compiler_dir, settings_file, command_packages)

        self.__error = ErrorHandler(self.__environment)
        self.__warning = WarningHandler(self.__environment)

    def generateExternalSourceCode(self, output: typez.Path):
        buffer = ""
        buffer += utils.Generate.fancyComment("BYTELANG COMMANDS HEADERS")

        array_data = list()

        max_name_length = utils.String.getMaxStringLen(list(self.__environment.COMMANDS.keys()))
        max_signature_length = utils.String.getMaxStringLen(list(CommandUnit.SIGNATURES.keys()))

        source_buffer = ""
        source_buffer += utils.Generate.fancyComment("SOURCE")

        command_prefix = "c_"

        for name, command in self.__environment.COMMANDS.items():
            source_buffer += utils.Generate.void_function_void(name, name_prefix=command_prefix, comment=command.signature)
            buffer += utils.Generate.void_function_void(name, name_prefix=command_prefix, header=True)
            array_data.append(
                f"{{ {command_prefix}{name:<{max_name_length}}, {command.signature.upper():<{max_signature_length}}, \"{command.identifier.upper()}\" }}"
            )

        buffer += "\n"

        buffer += utils.Generate.array("vm_commands", "vm_command_t", array_data, static=True, define_length=True,
                                       define_size=True, indexed=True)

        buffer += source_buffer

        utils.File.save(output, buffer)
        
    def getCommands(self) -> dict:
        return self.__environment.COMMANDS

    def compile(self, source_file: typez.Path, output_file: typez.Path) -> typez.CompiledProgram:
        self.__environment.setFiles(source_file, output_file)

        tokens = Tokenizer(self.__environment).run(utils.File.read(source_file))
        command_queue = Parser(self.__environment, self.__error, self.__warning).run(tokens)
        program_data = Translator(self.__environment, self.__error, self.__warning).run(command_queue)

        utils.File.saveBinary(output_file, program_data)

        return program_data

    def getLog(self) -> str:
        buf = utils.String.Buffer()

        buf.write(f"[ ByteLang Compiler v{self.__VERSION_MAJOR}.{self.__VERSION_MINOR}+{self.__VERSION_PATCH} ]")

        # COMPILER INFO

        buf.write(f"dir: {self.__environment.COMPILER_DIR}")

        # SETTINGS INFO

        buf.write(f"\n[Settings]\nfile: {self.__environment.SETTINGS_FILE}")

        buf.write(f"max program size: {self.__environment.MAX_PROGRAM_MEMORY} (bytes)")
        buf.write(f"max heap size: {self.__environment.MAX_HEAP_SIZE} (bytes)")
        buf.write(f"Comment token: '{self.__environment.CHAR_COMMENT}'")
        buf.write(f"signatures:\n{utils.String.tableFromDict(self.__environment.COMMAND_SIGNATURES, indent=2)}")

        # DIRECTIVES

        buf.write(f"\n[Directives]\nfile: {self.__environment.DIRECTIVES_FILE}")
        buf.write(f"loaded:\n{utils.String.fromList(self.__environment.DIRECTIVES.getLoaded(), name_format=f'{self.__environment.CHAR_DIRECTIVE}%s', indent=2)}")

        # COMMAND PACKAGES

        buf.write(f"\n[Command Packages]\ndir: {self.__environment.COMMAND_PACKAGES_DIR}")
        buf.write(f"used:\n{utils.String.fromList(self.__environment.COMMAND_PACKAGES_USE, indent=2)}")

        # COMPILE PROCESS

        buf.write(f"\n[Compilation]\nSource file: {self.__environment.source_file}\nOutput file: {self.__environment.output_file}")
        buf.write(f"compiled program size: {self.__environment.program_size} (bytes)\nheap index: {self.__environment.heap_index}")

        buf.write(f"program variables:\n{utils.String.fromList(list(self.__environment.variables.values()), indent=2)}")
        buf.write(f"macro constants:\n{utils.String.tableFromDict(self.__environment.macro_constants, indent=2)}")

        # WARNINGS

        buf.write(f"\n[Warnings]:\n{self.__warning.getLog()}")

        return buf.toString()

"""
BYTELANG 5 — Техническая документация

1. Типы файлов:
    - .bls — исходный байткод (ByteLang Source)

    - .blc — скомпилированный байткод (ByteLang Compiled)
        двоичный формат

    - .blp — пакет команд (ByteLang Package)
        Инструкции объявляются следующим образом:
            имя тип1 тип2 ...

        Недопустимы повторяющиеся идентификаторы

    - json (Параметры платформы) :
        Существуют следующие настройки:
        description     - описание пакета
        program_ptr     - Размер в байтах указателя программы (n) => 2^n >= P макс размер программы
        program_max_len - Максимальный размер скомпилированной программы
        instruction_ptr - Размер в байтах указателя инструкции -> макс кол-во инструкций
        heap_ptr        - Размер в байтах указателя кучи -> макс. размер кучи

2. Ограничение на одну команду в строке:
    каждая команда должна быть записана в отдельной строке.

3. Комментарии:
    Для добавления комментариев используется символ «;». Пример:
    ; Это комментарий

4. Директивы:
    Директивы используются для выполнения специальных функций.
    Формат директивы:.directive arg1 arg2
    Пример:.directive arg1 arg2

    Существующие директивы

    use <package path> - использовать пакет ByteLang
    platform <platform_json> - компиляция под конфигурацию платформы
    heap <size> - выделить память в кучи
    ptr <T> <name> <index> - объявить указатель name на тип T по адресу index
    inline <cmd> - последний аргумент* команды будет встроен в код, *если аргумент является указателем
    define <name> <value>

5. Команды:
    Команды выполняют определенные действия.
    Формат команды: command_name arg1 arg2
    Пример:
    command_name arg1 arg2

6. Метки:
    Метки используются для обозначения определенных точек в коде.
    Формат метки: mark:
    Пример:
    mark:


Каждый идентификатор является указателем на данные.
Запись
.ptr int8 abc 1
Означает, что идентификатор abc имеет адрес 1, который указывает на значение типа int8.

"""
import enum
import pathlib
import typing

import utils


class StatementType(enum.Enum):
    DIRECTIVE = enum.auto()
    MARK = enum.auto()
    INSTRUCTION = enum.auto()


class Statement:

    def __init__(self, _type: StatementType, lexeme: str, args: list[str], line: int):
        self.type = _type
        self.lexeme = lexeme
        self.args = args
        self.line = line

    def __repr__(self):
        return f"{self.type} {self.lexeme}{self.args}#{self.line}"


class ByteLangError(Exception):
    pass


class Argument:
    """Аргумент инструкции"""

    POINTER_CHAR = "*"

    def __init__(self, data_type: str, is_reference: bool):
        self.type: typing.Final[str] = data_type
        """Идентификатор типа аргумента"""
        self.pointer: typing.Final[bool] = is_reference
        """Передаётся ли аргумент по указателю или значению"""

        self.__string = f"{self.type}"
        if self.pointer:
            self.__string += self.POINTER_CHAR

    def __repr__(self):
        return self.__string


class Instruction:
    """Инструкция"""

    def __init__(self, package: str, identifier: str, index: int, args: tuple[Argument]):
        self.signature: typing.Final[tuple[Argument]] = args
        """Сигнатура"""
        self.identifier: typing.Final[str] = identifier
        """Уникальный строчный идентификатор инструкции"""
        self.index: typing.Final[int] = index
        """Уникальный индекс инструкции"""
        self.can_inline: typing.Final[bool] = len(self.signature) > 0 and self.signature[-1].pointer == True
        """Может ли последний аргумент инструкции быть поставлен по значению?"""
        self.__string = f"{package}::{self.identifier}#{self.index}{self.signature}"

    def __repr__(self):
        return self.__string


class Package:
    """Пакет инструкций"""

    def __init__(self, package_path: str):
        self.PATH: str = package_path
        """Путь к пакету"""
        self.NAME: str = pathlib.Path(package_path).stem
        """Уникальный идентификатор пакета"""
        self.INSTRUCTIONS: typing.Final[dict[str, Instruction]] = self.__loadInstructions()
        """Набор инструкций"""

    def __repr__(self):
        return f"Package '{self.NAME}' from '{self.PATH}' instructions: {self.INSTRUCTIONS}"

    def __parseInstruction(self, identifier, args):
        signature = list[Argument]()

        for arg_i, arg in enumerate(args):
            ref = False

            if Argument.POINTER_CHAR == arg[-1]:
                arg = arg[:-1]
                ref = True

            if not utils.Bytes.typeExist(arg):
                raise ByteLangError(f"Error in package '{self.PATH}', Instruction '{identifier}{args}', at arg: {arg_i} unknown type: '{arg}'")

            signature.append(Argument(arg, ref))

        return tuple[Argument](signature)

    def __loadInstructions(self):
        package_values = utils.File.readPackage(self.PATH)

        return {
            identifier: Instruction(
                self.NAME,
                identifier,
                index,
                self.__parseInstruction(identifier, signature)
            )
            for index, (identifier, signature) in enumerate(package_values)
        }


class Platform:

    def __init__(self, json_path: str):
        self.PATH: typing.Final[str] = json_path
        """путь к конфигурации платформы"""
        self.NAME: typing.Final[str] = pathlib.Path(json_path).stem
        """имя конфигурации"""
        self.DATA: typing.Final[dict[str, int | str]] = utils.File.readJSON(self.PATH)
        """Параметры платформы"""

    def __repr__(self):
        return f"Platform '{self.NAME}' from '{self.PATH}' data={self.DATA}"


class ContextManager:

    def __init__(self, P):
        self.P = P
        self.__loaded = dict[str, P]()
        self.used: P | None = None

    def load(self, path: str):
        _l = self.P(path)
        self.__loaded[_l.NAME] = _l

    def use(self, name: str):
        if (u := self.__loaded.get(name)) is None:
            raise ByteLangError(f"unknown {self.P} identifier: {name}")

        self.used = u


class ByteLangCompiler:

    def __init__(self):
        self.COMMENT_CHAR = ';'
        self.DIRECTIVE_CHAR = '.'
        self.MARK_CHAR = ':'

        self.packages = ContextManager(Package)
        self.platforms = ContextManager(Platform)

    def tokenize(self, source) -> list[Statement]:
        buffer = list()
        source_lines = source.split("\n")

        for index, line in enumerate(source_lines):
            if (line_no_comment := line.split(self.COMMENT_CHAR)[0].strip()) != "":
                lexeme, *args = line_no_comment.split()

                _type = None

                if lexeme[-1] == self.MARK_CHAR:
                    _type = StatementType.MARK
                    lexeme = lexeme[:-1]

                elif lexeme[0] == self.DIRECTIVE_CHAR:
                    lexeme = lexeme[1:]
                    _type = StatementType.DIRECTIVE

                elif lexeme in self.packages.used.INSTRUCTIONS.keys():  # command exists
                    _type = StatementType.INSTRUCTION

                else:
                    raise ByteLangError(f"Invalid Statement: '{lexeme}' at Line {index} '{line}'")

                buffer.append(Statement(_type, lexeme, args, index + 1))

        return buffer

    def parse(self, statements: list[Statement]):
        pass

    def execute(self, input_path: str, output_path: str):
        if self.packages.used is None:
            raise ByteLangError("need to select package")

        if self.platforms.used is None:
            raise ByteLangError("need to select platform")

        source = utils.File.read(input_path)

        tokens = self.tokenize(source)

        print(tokens)

        program = bytes()

        utils.File.saveBinary(output_path, program)

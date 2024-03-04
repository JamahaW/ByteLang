"""
BYTELANG 5 — Техническая документация

1. Типы файлов:
    — .bl — текстовый файл исходного байткода
    — .blc — скомпилированный байткод

2. Ограничение на одну команду в строке:
    каждая команда должна быть записана в отдельной строке.

3. Комментарии:
    Для добавления комментариев используется символ «;». Пример:
    ; Это комментарий

4. Директивы:
    Директивы используются для выполнения специальных функций.
    Формат директивы: .directive arg1 arg2
    Пример:.directive arg1 arg2

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

import BetaPy.utils


class TokenType(enum.Enum):
    DIRECTIVE = enum.auto()
    MARK = enum.auto()
    INSTRUCTION = enum.auto()


class Token:

    def __init__(self, _type: TokenType, lexeme: str, args: list[str], line: int):
        self.type = _type
        self.lexeme = lexeme
        self.args = args
        self.line = line

    def __repr__(self):
        return f"{self.type} {self.lexeme}{self.args}#{self.line}"


class ByteLangInitError(Exception):
    pass


class Instruction:

    def __init__(self, package: str, identifier: str, index: int, args: list[str], inlining: bool):
        if not BetaPy.utils.Bytes.typesExist(args) and args[-1] != "":
            raise ByteLangInitError(f"invalid type: {args}")

        self.signature = args
        self.inlining = inlining
        self.identifier = identifier
        self.index = index
        self.__string = f"{package}::{self.identifier}#{self.index}({' '.join(self.signature)})"

    def __repr__(self):
        return self.__string


class ByteLangCompiler:

    def __init__(self):
        self.COMMENT_CHAR = ';'
        self.DIRECTIVE_CHAR = '.'
        self.MARK_CHAR = ':'

        self.instructions = None

    def setInstructionPackage(self, package_path: str):
        package_json = BetaPy.utils.File.readJSON(package_path)

        self.instructions = dict[str, Instruction]()

        package_name = package_path.split(".")[0]

        for index, (identifier, value) in enumerate(package_json.items()):
            self.instructions[identifier] = Instruction(package_name, identifier, index, value["args"].split(" "), value["in"])

    def tokenize(self, source) -> list[Token]:
        buffer = list()
        source_lines = source.split("\n")

        for index, line in enumerate(source_lines):
            if (line_no_comment := line.split(self.COMMENT_CHAR)[0].strip()) != "":
                lexeme, *args = line_no_comment.split()

                _type = None

                if lexeme[-1] == self.MARK_CHAR:
                    _type = TokenType.MARK
                    lexeme = lexeme[:-1]

                elif lexeme[0] == self.DIRECTIVE_CHAR:
                    lexeme = lexeme[1:]
                    _type = TokenType.DIRECTIVE

                elif lexeme in self.instructions.keys():  # command exists
                    _type = TokenType.INSTRUCTION

                buffer.append(Token(_type, lexeme, args, index + 1))

        return buffer

    def execute(self, source: str):
        tokens = self.tokenize(source)

        ret = tokens

        return ret

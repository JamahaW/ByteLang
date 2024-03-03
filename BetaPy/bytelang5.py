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
"""
import enum


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


class ByteLangCompiler:

    def __init__(self):
        self.COMMENT_CHAR = ';'
        self.DIRECTIVE_CHAR = '.'
        self.MARK_CHAR = ':'

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

                else:
                    _type = TokenType.INSTRUCTION

                buffer.append(Token(_type, lexeme, args, index + 1))

        return buffer

    def execute(self, source: str):
        tokens = self.tokenize(source)

        return tokens

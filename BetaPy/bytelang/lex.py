import enum
import typing


class StatementType(enum.Enum):
    DIRECTIVE = enum.auto()
    MARK = enum.auto()
    INSTRUCTION = enum.auto()


class Statement:
    """Выражение"""

    def __init__(self, _type: StatementType, lexeme: str, args: list[str], line: int):
        self.type = _type
        self.lexeme = lexeme
        self.args = args
        self.line = line

    def __repr__(self):
        return f"{self.type} {self.lexeme}{self.args}#{self.line}"


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

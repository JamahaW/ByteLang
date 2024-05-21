import enum
import pathlib
from dataclasses import dataclass
from typing import Final

from . import utils
from .errors import ByteLangError


class Package:
    """Пакет инструкций"""

    def __init__(self, package_path: str):
        self.PATH: str = package_path
        """Путь к пакету"""
        self.NAME: str = pathlib.Path(package_path).stem
        """Уникальный идентификатор пакета"""
        self.INSTRUCTIONS: Final[dict[str, Instruction]] = self.__loadInstructions()
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
    """Характеристики платформы"""

    @dataclass(frozen=True, kw_only=True)
    class __Params:
        info: str
        prog_len: int
        ptr_prog: int
        ptr_heap: int
        ptr_inst: int

    def __init__(self, json_path: str):
        self.PATH: Final[str] = json_path
        """путь к конфигурации платформы"""
        self.NAME: Final[str] = pathlib.Path(json_path).stem
        """имя конфигурации"""

        self.DATA: Final[Platform.__Params] = Platform.__Params(**utils.File.readJSON(self.PATH))
        """Параметры платформы"""

    def __repr__(self):
        return f"Platform '{self.NAME}' from '{self.PATH}' data={self.DATA}"


class ContextLoader:
    """Менеджер загрузки контекста"""

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


class StatementType(enum.Enum):
    DIRECTIVE = enum.auto()
    MARK = enum.auto()
    INSTRUCTION = enum.auto()


@dataclass(repr=False, frozen=True, eq=False)
class Statement:
    """Выражение"""

    type: StatementType
    lexeme: str
    args: tuple[str, ...]
    line: int

    def __repr__(self):
        return f"{self.type} {self.lexeme}{self.args}#{self.line}"


class Argument:
    """Аргумент инструкции"""

    POINTER_CHAR = "*"

    def __init__(self, data_type: str, is_reference: bool):
        self.type: Final[str] = data_type
        """Идентификатор типа аргумента"""

        self.pointer: Final[bool] = is_reference
        """Передаётся ли аргумент по указателю или значению"""

        self.__string = f"{self.type}"

        if self.pointer:
            self.__string += self.POINTER_CHAR

    def __repr__(self):
        return self.__string

    def getSize(self, platform: Platform) -> int:
        return platform.DATA.ptr_heap if self.pointer else utils.Bytes.size(self.type)


class Instruction:
    """Инструкция"""

    def __init__(self, package: str, identifier: str, index: int, signature: tuple[Argument]):
        self.signature: Final[tuple[Argument]] = signature
        """Сигнатура"""

        self.identifier: Final[str] = identifier
        """Уникальный строчный идентификатор инструкции"""

        self.index: Final[int] = index
        """Уникальный индекс инструкции"""

        self.can_inline: Final[bool] = len(signature) > 0 and signature[-1].pointer == True
        """Может ли последний аргумент инструкции быть поставлен по значению?"""

        self.__string = f"{package}::{self.identifier}@{self.index}{self.signature}"

    def __repr__(self):
        return self.__string

    def getSize(self, platform: Platform, inlined: bool) -> int:
        """Размер скомпилированной инструкции в байтах"""

        arg_size = sum(map(lambda x: x.getSize(platform), (x for x in (self.signature[:-1] if inlined else self.signature))))
        d = utils.Bytes.size(self.signature[-1].type) * inlined

        return platform.DATA.ptr_inst + arg_size + d

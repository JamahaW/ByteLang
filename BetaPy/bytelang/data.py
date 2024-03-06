import pathlib
import typing

from . import utils
from .errors import ByteLangError
from .lex import Argument, Instruction


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
    """Характеристики платформы"""

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

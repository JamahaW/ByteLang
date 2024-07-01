"""
Различные Реестры контента
"""
from abc import ABC
from abc import abstractmethod
from typing import Final
from typing import Generic
from typing import Iterable
from typing import Optional
from typing import TypeVar

from bytelang.content import BasicInstruction
from bytelang.content import InstructionArgument
from bytelang.content import Package
from bytelang.content import Profile
from bytelang.tools import FileTool
from content import Environment

_T = TypeVar("_T")


# TODO произвольные регистры и НЕ файловые

class BasicRegistry(ABC, Generic[_T]):
    """
    Базовый Файловый Реестр[T]
    """

    def __init__(self, file_ext: str) -> None:
        self.__FILE_EXT: Final[str] = file_ext
        self.__folder: Optional[str] = None
        self.__data = dict[str, _T]()

    # TODO использовать какой-то там умный класс для каталога

    def setFolder(self, folder: str) -> None:
        self.__folder = folder

    def get(self, name: str) -> _T:
        """
        Получить контент по содержимому
        :param name:
        """

        if self.__folder is None:
            raise ValueError(f"Cannot get {name}! Must set folder")

        if (ret := self.__data.get(name)) is None:
            ret = self.__data[name] = self._load(name)
            return ret

        return ret

    def _getFilepath(self, name: str) -> str:
        return f"{self.__folder}{name}.{self.__FILE_EXT}"

    @abstractmethod
    def _load(self, name: str) -> _T:
        """
        Загрузить контент
        :param name:
        """
        pass


class ProfileRegistry(BasicRegistry[Profile]):

    def _load(self, name: str) -> Profile:
        pass


class PackageRegistry(BasicRegistry[Package]):

    def _load(self, name: str) -> Package:
        filepath = self._getFilepath(name)

        return Package(
            parent=filepath,
            name=name,
            instructions=tuple(self.__parseInstructions(name, filepath))
        )

    def __parseInstructions(self, package_name: str, filepath: str) -> Iterable[BasicInstruction]:
        ret = list[BasicInstruction]()
        used_names = set[str]()

        for line in FileTool.read(filepath).split("\n"):
            line = line.split("#")[0].strip()

            if line == "":
                continue

            name, *arg_types = line.split()

            if name in used_names:
                raise ValueError(f"In ByteLang Instruction package '{self}' redefinition of '{name}'")

            ret.append(BasicInstruction(
                parent=package_name,
                name=name,
                arguments=tuple(self.__parseArgument(i, arg) for i, arg in enumerate(arg_types))
            ))

            used_names.add(name)

        return ret

    def __parseArgument(self, index: int, arg_lexeme: str) -> InstructionArgument:
        pass  # TODO доделать


class EnvironmentsRegistry(BasicRegistry[Environment]):

    def __init__(self, file_ext: str, profiles: ProfileRegistry, packages: PackageRegistry) -> None:
        super().__init__(file_ext)
        self.profileRegistry = profiles
        self.packageRegistry = packages

    def _load(self, name: str) -> Environment:
        filepath = self._getFilepath(name)
        data = FileTool.readJSON(filepath)

        return Environment(
            parent=filepath,
            name=name,
            profile=self.profileRegistry.get(data["profile"]),
            instructions=tuple(data["packages"])  # TODO реализовать нормально
        )

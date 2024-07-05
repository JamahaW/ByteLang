"""
Различные Реестры контента
"""
from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from os import PathLike
from pathlib import Path
from struct import Struct
from typing import Final
from typing import Generic
from typing import Iterable
from typing import Optional
from typing import TypeVar

from bytelang.content import Environment
from bytelang.content import EnvironmentInstruction
from bytelang.content import PackageInstructionArgument
from bytelang.content import Package
from bytelang.content import PackageInstruction
from bytelang.content import PrimitiveType
from bytelang.content import PrimitiveWriteType
from bytelang.content import Profile
from bytelang.parsers import Parser
from bytelang.tools import FileTool
from bytelang.tools import ReprTool

_T = TypeVar("_T")
"""content Type"""
_K = TypeVar("_K")
"""content Key"""
_R = TypeVar("_R")
"""content Raw object"""


# TODO реализовать реестры
#  Реестры с временным хранением данных, возможностью их удаления (Тупо словарь?)
#  переменных
#  констант


class Registry(ABC, Generic[_K, _T]):
    """
    Базовый реестр
    """

    def __init__(self):
        self._data = dict[_K, _T]()

    def getValues(self) -> Iterable[_T]:
        return self._data.values()

    @abstractmethod
    def get(self, __key: _K) -> _T:
        """
        Получить контент
        :param __key:
        :return: None если контент не найден
        """


class JSONFileRegistry(Registry[str, _T], Generic[_R, _T]):
    """
    Реестр, сразу заполнивший значения из JSON-файла
    """

    def __init__(self):
        super().__init__()
        self._filepath: Optional[Path] = None

    def setFile(self, filepath: PathLike | str) -> None:
        self._filepath = Path(filepath)
        self._data.clear()
        self._data.update(
            {
                name: self._parse(name, raw)
                for name, raw in FileTool.readJSON(self._filepath).items()
            }
        )

    def get(self, __key: str) -> Optional[_T]:
        if self._filepath is None:
            raise ValueError("Must select File")

        return self._data.get(__key)

    @abstractmethod
    def _parse(self, name: str, raw: _R) -> _T:
        """
        Преобразовать сырое представление в объект контента
        :param raw:
        :return:
        """


_PrimitiveRaw = dict[str, int | str]


class PrimitiveTypeRegistry(JSONFileRegistry[_PrimitiveRaw, PrimitiveType]):
    """
    Реестр примитивных типов
    """

    def __init__(self):
        super().__init__()
        self.__primitives_by_size = dict[tuple[int, PrimitiveWriteType], PrimitiveType]()

    def getBySize(self, size: int, write_type: PrimitiveWriteType = PrimitiveWriteType.unsigned) -> PrimitiveType:
        return self.__primitives_by_size[size, write_type]

    def _parse(self, name: str, raw: _PrimitiveRaw) -> PrimitiveType:
        size = raw["size"]
        write_type = PrimitiveWriteType[raw["type"]]

        if (size, write_type) in self.__primitives_by_size.keys():
            raise ValueError(f"type aliases not support: {name}, {raw}")

        formats = PrimitiveType.EXPONENT_FORMATS if write_type == PrimitiveWriteType.exponent else PrimitiveType.INTEGER_FORMATS

        if (fmt := formats.get(size)) is None:
            raise ValueError(f"Invalid size ({size}) must be in {tuple(formats.keys())}")

        if write_type == PrimitiveWriteType.signed:
            fmt = fmt.lower()

        ret = self.__primitives_by_size[size, write_type] = PrimitiveType(
            name=name,
            parent=self._filepath.stem,
            size=size,
            write_type=write_type,
            packer=Struct(fmt)
        )

        return ret


class CatalogRegistry(Registry[str, _T]):
    """
    Каталоговый Реестр[T] (ищет файл по имени в каталоге)
    """

    def __init__(self, file_ext: str) -> None:
        super().__init__()
        self.__FILE_EXT: Final[str] = file_ext
        self.__folder: Optional[Path] = None

    def setFolder(self, folder: PathLike | str) -> None:
        """Установить каталог для загрузки контента"""
        self.__folder = Path(folder)

        if not self.__folder.is_dir():
            raise ValueError(f"Not a Folder: {folder}")

        self._data.clear()

    def get(self, name: str) -> _T:
        if self.__folder is None:
            raise ValueError(f"Cannot get {name}! Must set folder")

        if (ret := self._data.get(name)) is None:
            filepath = str(self.__folder / f"{name}.{self.__FILE_EXT}")
            ret = self._data[name] = self._load(filepath, name)

        return ret

    @abstractmethod
    def _load(self, filepath: str, name: str) -> _T:
        """
        Загрузить контент из файла
        :param filepath: путь к этому контенту
        :param name: его наименование
        :return:
        """


class ProfileRegistry(CatalogRegistry[Profile]):

    def __init__(self, file_ext: str, primitives: PrimitiveTypeRegistry):
        super().__init__(file_ext)
        self.__primitive_type_registry = primitives

    def _load(self, filepath: str, name: str) -> Profile:
        data = FileTool.readJSON(filepath)

        def getType(t: str) -> PrimitiveType:
            return self.__primitive_type_registry.getBySize(data[t])

        return Profile(
            parent=filepath,
            name=name,
            max_program_length=data.get("prog_len"),
            pointer_program=getType("ptr_prog"),
            pointer_heap=getType("ptr_heap"),
            instruction_index=getType("ptr_inst"),
        )


class PackageParser(Parser[PackageInstruction]):
    """Парсер пакета инструкций"""

    def __init__(self, primitives: PrimitiveTypeRegistry):
        self.__used_names = set[str]()
        self.__package_name: Optional[str] = None
        self.__primitive_type_registry = primitives

    def begin(self, package_name: str) -> None:
        self.__package_name = package_name

    def _parseLine(self, index: int, line: str) -> Optional[PackageInstruction]:
        name, *arg_types = line.split()

        if name in self.__used_names:
            raise ValueError(f"redefinition of {self.__package_name}::{name}{ReprTool.iter(arg_types)} at line {index} ")

        self.__used_names.add(name)

        return PackageInstruction(
            parent=self.__package_name,
            name=name,
            arguments=tuple(
                self.__parseArgument(self.__package_name, name, i, arg)
                for i, arg in enumerate(arg_types)
            )
        )

    def __parseArgument(self, package_name: str, name: str, index: int, arg_lexeme: str) -> PackageInstructionArgument:
        is_pointer = arg_lexeme[-1] == PackageInstructionArgument.POINTER_CHAR
        arg_lexeme = arg_lexeme.rstrip(PackageInstructionArgument.POINTER_CHAR)

        if (primitive := self.__primitive_type_registry.get(arg_lexeme)) is None:
            raise ValueError(f"Unknown primitive '{arg_lexeme}' at {index} in {package_name}::{name}")

        return PackageInstructionArgument(primitive=primitive, is_pointer=is_pointer)


class PackageRegistry(CatalogRegistry[Package]):

    def __init__(self, file_ext: str, primitives: PrimitiveTypeRegistry):
        super().__init__(file_ext)
        self.__lexer = PackageParser(primitives)

    def _load(self, filepath: str, name: str) -> Package:
        self.__lexer.begin(name)

        with open(filepath) as f:
            return Package(parent=filepath, name=name, instructions=tuple(self.__lexer.run(f)))


class EnvironmentsRegistry(CatalogRegistry[Environment]):

    def __init__(self, file_ext: str, profiles: ProfileRegistry, packages: PackageRegistry) -> None:
        super().__init__(file_ext)
        self.__profile_registry = profiles
        self.__package_registry = packages

    def _load(self, filepath: str, name: str) -> Environment:
        data = FileTool.readJSON(filepath)
        profile = self.__profile_registry.get(data["profile"])

        return Environment(
            parent=filepath,
            name=name,
            profile=profile,
            instructions=self.__processPackages(profile, data["packages"])
        )

    def __processPackages(self, profile: Profile, packages_names: Iterable[str]) -> dict[str, EnvironmentInstruction]:
        ret = dict[str, EnvironmentInstruction]()
        index: int = 0

        for package_name in packages_names:
            for ins in self.__package_registry.get(package_name).instructions:
                if (ex_ins := ret.get(ins.name)) is not None:
                    raise ValueError(f"{ins} - overload is not allowed ({ex_ins} defined already)")

                ret[ins.name] = ins.transform(index, profile)
                index += 1

        return ret

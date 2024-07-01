"""
Различные Реестры контента
"""

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

from bytelang.content import BasicInstruction
from bytelang.content import Environment
from bytelang.content import EnvironmentInstruction
from bytelang.content import InstructionArgument
from bytelang.content import Package
from bytelang.content import PrimitiveType
from bytelang.content import Profile
from bytelang.tools import FileTool

_T = TypeVar("_T")  # content Type
_K = TypeVar("_K")  # content Key
_R = TypeVar("_R")  # content Raw object


class BasicRegistry(ABC, Generic[_K, _T]):
    """
    Базовый реестр
    """

    def __init__(self):
        self._data = dict[_K, _T]()

    def getValues(self) -> Iterable[_T]:
        return self._data.values()

    @abstractmethod
    def get(self, __key: _K) -> Optional[_T]:
        """
        Получить контент
        :param __key:
        :return: None если контент не найден
        """


class JSONFileRegistry(BasicRegistry[str, _T], Generic[_R, _T]):
    """
    Реестр, сразу заполнивший значения из JSON-файла
    """

    def __init__(self):
        super().__init__()
        self._filepath: Optional[Path] = None

    def setFile(self, filepath: PathLike | str) -> None:
        filepath = Path(filepath)

        self._filepath = filepath
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


_PrimitiveRaw = dict[str, int | bool]


class PrimitiveTypeRegistry(JSONFileRegistry[_PrimitiveRaw, PrimitiveType]):
    """
    Реестр примитивных типов
    """

    # TODO float
    _STRUCT_FORMATS_BY_SIZE: Final[dict[int, str]] = {
        1: "B",
        2: "H",
        4: "I",
        8: "Q"
    }

    def __init__(self):
        super().__init__()
        self.__next_index: int = 0
        self.__primitives_by_size = dict[tuple[int, bool], PrimitiveType]()

    def getBySize(self, size: int, signed=False) -> PrimitiveType:
        return self.__primitives_by_size[size, signed]

    def _parse(self, name: str, raw: _PrimitiveRaw) -> PrimitiveType:
        size = raw["size"]

        if (fmt := self._STRUCT_FORMATS_BY_SIZE.get(size)) is None:
            raise ValueError(f"Invalid size ({size}) must be in {tuple(self._STRUCT_FORMATS_BY_SIZE.keys())}")

        signed = raw["signed"]

        if (size, signed) in self.__primitives_by_size.keys():
            raise ValueError(f"type aliases not support: {name}, {raw}")

        ret = PrimitiveType(
            name=name,
            parent=self._filepath.stem,
            index=self.__next_index,
            size=size,
            signed=signed,
            packer=Struct(fmt.lower() if signed else fmt)
        )

        self.__primitives_by_size[size, signed] = ret
        self.__next_index += 1

        return ret


# TODO setFolder передать маску с расширением файла
class CatalogRegistry(BasicRegistry[str, _T]):
    """
    Каталоговый Реестр[T] (ищет файл по имени в каталоге)
    """

    def __init__(self, file_ext: str) -> None:
        super().__init__()
        self.__FILE_EXT: Final[str] = file_ext
        self.__folder: Optional[Path] = None

    def setFolder(self, folder: PathLike | str) -> None:
        """Установить каталог для загрузки контента"""
        folder = Path(folder)

        if not folder.is_dir():
            raise ValueError(f"Not a Folder: {folder}")

        self.__folder = folder

    def get(self, name: str) -> Optional[_T]:
        if self.__folder is None:
            raise ValueError(f"Cannot get {name}! Must set folder")

        if (ret := self._data.get(name)) is None:
            filepath = str(self.__folder / f"{name}.{self.__FILE_EXT}")
            ret = self._data[name] = self._load(filepath, name)

        return ret

    @abstractmethod
    def _load(self, filepath: str, name: str) -> Optional[_T]:
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

    def _load(self, filepath: str, name: str) -> Optional[Profile]:
        data = FileTool.readJSON(filepath)

        def get_type(t: str) -> PrimitiveType:
            return self.__primitive_type_registry.getBySize(data[t])

        return Profile(
            parent=filepath,
            name=name,
            max_program_length=data.get("prog_len"),
            pointer_program=get_type("ptr_prog"),
            pointer_heap=get_type("ptr_heap"),
            instruction_index=get_type("ptr_inst"),
            type_index=get_type("ptr_type")
        )


class PackageRegistry(CatalogRegistry[Package]):
    POINTER_CHAR: Final[str] = "*"

    def __init__(self, file_ext: str, primitives: PrimitiveTypeRegistry):
        super().__init__(file_ext)
        self.__primitive_type_registry = primitives

    def _load(self, filepath: str, name: str) -> Optional[Package]:
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
                raise ValueError(f"redefinition of '{name}' in package '{package_name}' ")

            ret.append(BasicInstruction(
                parent=package_name,
                name=name,
                arguments=tuple(self.__parseArgument(package_name, name, i, arg) for i, arg in enumerate(arg_types))
            ))

            used_names.add(name)

        return ret

    def __parseArgument(self, package_name: str, name: str, index: int, arg_lexeme: str) -> InstructionArgument:
        is_pointer = arg_lexeme[-1] == self.POINTER_CHAR

        if (primitive := self.__primitive_type_registry.get(arg_lexeme.rstrip(self.POINTER_CHAR))) is None:
            raise ValueError(f"Unknown primitive '{arg_lexeme}' at {index} in {package_name}::{name}")

        return InstructionArgument(
            primitive=primitive,
            is_pointer=is_pointer
        )


class EnvironmentsRegistry(CatalogRegistry[Environment]):

    def __init__(self, file_ext: str, profiles: ProfileRegistry, packages: PackageRegistry) -> None:
        super().__init__(file_ext)
        self.__profile_registry = profiles
        self.__package_registry = packages

    def _load(self, filepath: str, name: str) -> _T:
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
                    raise ValueError(f"{ins} - overload not possible ({ex_ins} defined already)")

                ret[ins.name] = EnvironmentInstruction(
                    parent=profile.name,
                    name=ins.name,
                    index=index,
                    package=package_name,
                    arguments=tuple(
                        InstructionArgument(
                            primitive=profile.pointer_heap if arg.is_pointer else arg.primitive,
                            is_pointer=arg.is_pointer
                        )
                        for arg in ins.arguments
                    )
                )

                index += 1

        return ret

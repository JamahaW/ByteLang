"""
Различные Реестры контента
"""
from abc import ABC
from abc import abstractmethod
from pathlib import Path
from struct import Struct
from typing import Final
from typing import Generic
from typing import Iterable
from typing import Optional
from typing import TypeVar

from bytelang.content import BasicInstruction
from bytelang.content import Environment
from bytelang.content import InstructionArgument
from bytelang.content import Package
from bytelang.content import PrimitiveType
from bytelang.content import Profile
from bytelang.tools import FileTool
from bytelang.tools import ReprTool

_T = TypeVar("_T")  # content Type
_K = TypeVar("_K")  # content Key
_R = TypeVar("_R")  # content Raw object


class BasicRegistry(ABC, Generic[_K, _T]):
    """
    Базовый реестр
    """

    def __init__(self):
        self._data = dict[_K, _T]()

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

    def setFile(self, filepath: str) -> None:
        filepath = Path(filepath)

        if not filepath.is_file():
            raise ValueError(f"Not a File: {filepath}")

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


class CatalogRegistry(BasicRegistry[str, _T]):
    """
    Каталоговый Реестр[T] (ищет файл по имени в каталоге)
    """

    def __init__(self, file_ext: str) -> None:
        super().__init__()
        self.__FILE_EXT: Final[str] = file_ext
        self.__folder: Optional[Path] = None

    def setFolder(self, folder: str) -> None:
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

    def __init__(self, file_ext: str, primitiveTypeRegistry: PrimitiveTypeRegistry):
        super().__init__(file_ext)
        self.__primitiveTypeRegistry = primitiveTypeRegistry

    def _load(self, filepath: str, name: str) -> Optional[Profile]:
        data = FileTool.readJSON(filepath)

        def get_type(t: str) -> PrimitiveType:
            return self.__primitiveTypeRegistry.getBySize(data[t])

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

    def __init__(self, file_ext: str, primitiveTypeRegistry: PrimitiveTypeRegistry):
        super().__init__(file_ext)
        self.__primitiveTypeRegistry = primitiveTypeRegistry

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

        if (primitive := self.__primitiveTypeRegistry.get(arg_lexeme.rstrip(self.POINTER_CHAR))) is None:
            raise ValueError(f"Unknown primitive '{arg_lexeme}' at {index} in {package_name}::{name}")

        return InstructionArgument(
            primitive=primitive,
            is_pointer=is_pointer
        )


class EnvironmentsRegistry(CatalogRegistry[Environment]):

    def __init__(self, file_ext: str, profiles: ProfileRegistry, packages: PackageRegistry) -> None:
        super().__init__(file_ext)
        self.__profileRegistry = profiles
        self.__packageRegistry = packages

    def _load(self, filepath: str, name: str) -> _T:
        data = FileTool.readJSON(filepath)
        # TODO
        #  реализовать нормально
        #  Из пакетов формируется единый блок инструкций окружения

        return Environment(
            parent=filepath,
            name=name,
            profile=self.__profileRegistry.get(data["profile"]),
            instructions=tuple(data["packages"])
        )


if __name__ == '__main__':
    fp = r"A:\Projects\ByteLang\registries_data\primitive_types.json"

    prim = PrimitiveTypeRegistry()
    prim.setFile(fp)

    # prof = ProfileRegistry("json", prim)
    # prof.setFolder(r"A:\Projects\ByteLang\registries_data\profiles")
    #
    # av = prof.get("avr")
    #
    # print(ReprTool.column(av.__dict__.items()))

    pack = PackageRegistry("blp", prim)
    pack.setFolder(r"A:\Projects\ByteLang\registries_data\packages")

    p1 = pack.get("io")

    print(p1)



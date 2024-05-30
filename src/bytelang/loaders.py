from __future__ import annotations

from typing import TypeVar, Generic, Final, Optional

from .data import Package, Platform
from .errors import *
from .tools import FileTool

_T = TypeVar('_T')


class __Loader(Generic[_T]):

    def __init__(self, target_folder: str, file_ext: str):
        self.FOLDER: Final[str] = target_folder
        self.EXT: Final[str] = file_ext.lower()
        self.current: Optional[_T] = None
        self.loaded: dict[str, Optional[_T]] = {
            name: None
            for name in FileTool.getFileNamesByExt(target_folder, file_ext)
        }

    def use(self, name: str) -> None:
        if name not in self.loaded.keys():
            raise ByteLangError(f"could not find '{name}'({self.EXT}) from {self.FOLDER}")

        if (loaded := self.loaded.get(name)) is None:
            loaded = self.loaded[name] = self._load(f"{self.FOLDER}{name}.{self.EXT}")

        self.current = loaded

    def _load(self, filename: str) -> _T:
        pass


class PackageLoader(__Loader[Package]):

    def __init__(self, target_folder: str):
        super().__init__(target_folder, "blp")

    def _load(self, filename: str) -> Package:
        return Package(filename)


class PlatformLoader(__Loader[Platform]):
    def __init__(self, target_folder: str):
        super().__init__(target_folder, "json")

    def _load(self, filename: str) -> Platform:
        return Platform(filename)

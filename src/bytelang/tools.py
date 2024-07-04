from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from typing import Iterable
from typing import Mapping
from typing import Optional
from typing import TypeVar

_T = TypeVar("_T")


class Filter:

    @staticmethod
    def notNone(i: Iterable[Optional[_T]]) -> Iterable[_T]:
        return filter(None.__ne__, i)


class FileTool:
    """Обёртка для работы с файлами"""

    @classmethod
    def read(cls, filepath: str) -> str:
        with open(filepath, "rt") as f:
            return f.read()

    @classmethod
    def readBytes(cls, filepath: str) -> bytes:
        with open(filepath, "rb") as f:
            return f.read()

    @classmethod
    def readJSON(cls, filepath: str | Path) -> dict | list:
        with open(filepath) as f:
            return json.load(f)

    @classmethod
    def save(cls, filepath: str, _data: str):
        with open(filepath, "wt") as f:
            f.write(_data)

    @classmethod
    def saveBytes(cls, filepath: str, _data: bytes):
        with open(filepath, "wb") as f:
            f.write(_data)


class ReprTool:

    @staticmethod
    def __viewMode(obj: object, _repr: bool) -> str:
        return obj.__repr__() if _repr else obj.__str__()

    @classmethod
    def iter(cls, iterable: Iterable, /, *, l_paren: str = "(", sep: str = ", ", r_paren: str = ")", _repr: bool = False) -> str:
        return f"{l_paren}{sep.join(cls.__viewMode(i, _repr) for i in iterable)}{r_paren}"

    @classmethod
    def column(cls, iterable: Iterable, /, *, sep: str = ": ", begin: int = 0, intend: int = 0, _repr: bool = False) -> str:
        return '\n'.join(f"{'  ' * intend}{(index + begin):>3}{sep}{cls.__viewMode(item, _repr)}" for index, item in enumerate(iterable))

    @classmethod
    def strDict(cls, _dict: Mapping[str, object], /, *, _round: int = 8, sep=": ", _repr: bool = False) -> str:
        k_len = max(map(len, _dict.keys())) // _round * _round + _round
        return '\n'.join(f"{key:{k_len}}{sep}{cls.__viewMode(value, _repr)}" for key, value in _dict.items())

    @staticmethod
    def title(title: str, /, *, length: int = 120, fill: str = "-") -> str:
        return f"{f' <<< {title} >>> ' :{fill}^{length}}"

    @classmethod
    def headed(cls, name: str, i: Iterable, /, *, length: int = 120, _repr: bool = False) -> str:
        return f"{cls.title(name, length=length)}\n{cls.column(i, _repr=_repr)}\n"

    @staticmethod
    def prettyBytes(b: bytes) -> str:
        return b.hex("_", 2).upper()


class StringBuilder(StringIO):

    def __init__(self) -> None:
        super().__init__()

    def append(self, obj: object, sep: str = "\n") -> StringBuilder:
        self.write(obj.__str__())
        self.write(sep)
        return self

    def __str__(self) -> str:
        return self.getvalue()

    def toString(self) -> str:
        return self.__str__()

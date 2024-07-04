import json
from pathlib import Path
from typing import Iterable
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
    def iter(iterable: Iterable, *, l_paren: str = "(", sep: str = ", ", r_paren: str = ")") -> str:
        return f"{l_paren}{sep.join(i.__str__() for i in iterable)}{r_paren}"

    @staticmethod
    def column(iterable: Iterable, *, sep: str = ": ", begin: int = 0, intend: int = 0) -> str:
        return '\n'.join(f"{'  ' * intend}{(index + begin):>3}{sep}{item}" for index, item in enumerate(iterable))

    @staticmethod
    def headed(name: str, i: Iterable, *, length: int = 120, fill: str = "-") -> str:
        return f"{f' <<< {name} >>> ':{fill}^{length}}\n{ReprTool.column(i)}\n"

    @staticmethod
    def prettyBytes(b: bytes) -> str:
        return b.hex("_", 2).upper()

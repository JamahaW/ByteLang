import json
from pathlib import Path
from typing import Iterable


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
    def readJSON(cls, filepath: str) -> dict | list:
        with open(filepath) as f:
            return json.load(f)

    @classmethod
    def save(cls, filepath: str, _data: str):
        with open(filepath, "wt") as f:
            f.write(_data)

    @classmethod
    def saveBinary(cls, filepath: str, _data: bytes):
        with open(filepath, "wb") as f:
            f.write(_data)

    @classmethod
    def getFileNamesByExt(cls, folder: str, extension: str) -> tuple[str, ...]:
        return tuple(file.stem for file in Path(folder).glob(f"*.{extension}"))


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


if __name__ == '__main__':
    print(FileTool.readJSON("../../data/environments/test_env.json"))

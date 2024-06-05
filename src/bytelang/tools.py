import json
from pathlib import Path
from typing import Iterable


class FileTool:
    """Обёртка для работы с файлами"""

    @staticmethod
    def __forFileExecute(filepath: str, mode: str, func):
        """
        Выполнить `func` для файла
        :param func: `lambda f`: ...
        :return: `ret = func(file)`
        """
        with open(filepath, mode) as file:
            ret = func(file)
        return ret

    @classmethod
    def __fileRead(cls, filepath: str, mode: str) -> str | bytes:
        """
        Прочесть файл с режимом `mode`
        :return: `file.read()`
        """
        return cls.__forFileExecute(filepath, mode, lambda file: file.read())

    @classmethod
    def __fileSave(cls, filepath: str, mode: str, _data: str | bytes):
        """
        Сохранить файл с режимом `mode`
        """
        cls.__forFileExecute(filepath, mode, lambda file: file.write(_data))

    @classmethod
    def read(cls, filepath: str) -> str:
        return cls.__fileRead(filepath, "r")

    @classmethod
    def readBinary(cls, filepath: str) -> bytes:
        return cls.__fileRead(filepath, "rb")

    @classmethod
    def save(cls, filepath: str, _data: str):
        cls.__fileSave(filepath, "w", _data)

    @classmethod
    def saveBinary(cls, filepath: str, _data: bytes):
        cls.__fileSave(filepath, "wb", _data)

    @classmethod
    def readJSON(cls, filepath: str) -> dict | list:
        return cls.__forFileExecute(filepath, "r", lambda file: json.load(file))

    @classmethod
    def getFileNamesByExt(cls, folder: str, extension: str) -> tuple[str]:
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


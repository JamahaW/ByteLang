import json


class File:
    """Обёртка для работы с файлами"""

    @staticmethod
    def __forFileExecute(filepath: str, mode: str, func):
        """
        выполнить `func` для файла
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
    def readPackage(cls, filepath: str) -> tuple[tuple[str, tuple[str]]]:
        """Прочесть пакет инструкций ByteLang"""
        ret = list()
        names_used = set[str]()

        lines = cls.read(filepath).split("\n")

        for line in lines:
            line = line.split("#")[0].strip()

            if line == "":
                continue

            name, *signature = line.split()

            if name in names_used:
                raise KeyError(f"In ByteLang Instruction package '{filepath}' redefinition of '{name}'")

            names_used.add(name)
            ret.append((name, signature))

        return tuple[tuple[str, tuple[str]]](ret)

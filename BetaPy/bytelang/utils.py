import json
import struct


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
            line = line.strip()

            if line == "":
                continue

            name, *signature = line.split()

            if name in names_used:
                raise KeyError(f"In ByteLang Instruction package '{filepath}' redefinition of '{name}'")

            names_used.add(name)
            ret.append((name, signature))

        return tuple[tuple[str, tuple[str]]](ret)


class Bytes:
    """Упаковка и распаковка двоичных структур """

    __TYPES = {"char": "c", "bool": "?", "i8": "b", "u8": "B", "i16": "h", "u16": "H", "i32": "i", "u32": "I", "i64": "q", "u64": "Q", "f32": "f", "f64": "d"}

    __RANGES = {
        "char": (-128, 127),
        "bool": (0, 1),
        "i8": (-128, 127),
        "u8": (0, 255),
        "i16": (-32768, 32767),
        "u16": (0, 65535),
        "i32": (-2147483648, 2147483647),
        "u32": (0, 4294967295),
        "i64": (-9223372036854775808, 9223372036854775807),
        "u64": (0, 18446744073709551615),
    }

    @classmethod
    def typeRange(cls, _type: str) -> tuple[int, int]:
        if (ret := cls.__RANGES.get(_type)) is not None:
            return ret
        raise ValueError(f"{_type} has not range")

    @classmethod
    def typeExist(cls, _type: str) -> bool:
        return _type in cls.__TYPES.keys()

    @classmethod
    def pack(cls, _format: str, _values: tuple) -> bytes:
        return struct.pack(cls.__translateTypeFormat(_format), *cls.__convertTypes(_values))

    @classmethod
    def unpack(cls, _format: str, _data: bytes) -> tuple:
        return tuple(cls.__reverseConvertTypes(struct.unpack(cls.__translateTypeFormat(_format), _data)))

    @classmethod
    def size(cls, _format: str) -> int:
        return struct.calcsize(cls.__translateTypeFormat(_format))

    @staticmethod
    def __convertTypes(_values: tuple) -> tuple:
        return tuple((bytes(val, encoding="utf-8") if isinstance(val, str) else val for val in _values))

    @staticmethod
    def __reverseConvertTypes(_values: tuple):
        return tuple((str(val, encoding="utf-8") if isinstance(val, bytes) else val for val in _values))

    @classmethod
    def __translateTypeFormat(cls, _format: str) -> str:
        return "".join((cls.__TYPES[fmt] for fmt in _format.split(" ")))


if __name__ == "__main__":
    pass

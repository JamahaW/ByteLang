import struct


class File:
    """Обёртка для работы с файлами"""

    @staticmethod
    def __fileGet(filepath: str, mode: str, func):
        with open(filepath, mode) as file:
            ret = func(file)
        return ret

    @classmethod
    def __fileRead(cls, filepath: str, mode: str) -> str:
        return cls.__fileGet(filepath, mode, lambda file: file.read())

    @classmethod
    def __fileSave(cls, filepath: str, mode: str, _data: str | bytes):
        cls.__fileGet(filepath, mode, lambda file: file.write(_data))

    @classmethod
    def read(cls, filepath: str):
        return cls.__fileRead(filepath, "r")

    @classmethod
    def readBinary(cls, filepath: str):
        return cls.__fileRead(filepath, "rb")

    @classmethod
    def save(cls, filepath: str, _data: str):
        cls.__fileSave(filepath, "w", _data)

    @classmethod
    def saveBinary(cls, filepath: str, _data: bytes):
        cls.__fileSave(filepath, "wb", _data)


class Bytes:
    """Упаковка и распаковка двоичных структур """

    __TYPES = {"char": "c", "int8": "b", "uint8": "B", "bool": "?", "int16": "h", "uint16": "H", "int32": "i", "uint32": "I", "int64": "q", "uint64": "Q", "float": "f", "double": "d"}

    @staticmethod
    def __convertTypes(_values: tuple) -> tuple:
        return tuple((bytes(val, encoding="utf-8") if isinstance(val, str) else val for val in _values))

    @staticmethod
    def __reverseConvertTypes(_values: tuple):
        return tuple((str(val, encoding="utf-8") if isinstance(val, bytes) else val for val in _values))

    @classmethod
    def __translateTypeFormat(cls, _format: str) -> str:
        return "".join((cls.__TYPES[fmt] for fmt in _format.split(" ")))

    @classmethod
    def pack(cls, _format: str, _values: tuple) -> bytes:
        return struct.pack(cls.__translateTypeFormat(_format), *cls.__convertTypes(_values))

    @classmethod
    def unpack(cls, _format: str, _data: bytes) -> tuple:
        return tuple(cls.__reverseConvertTypes(struct.unpack(cls.__translateTypeFormat(_format), _data)))

    @classmethod
    def size(cls, _format: str) -> int:
        return struct.calcsize(cls.__translateTypeFormat(_format))


if __name__ == "__main__":
    f = "uint8 int8 char"

    data = Bytes.pack(f, (
        155,
        -100,
        " "
    ))

    print(data)

    values = Bytes.unpack(f, data)

    print(values)

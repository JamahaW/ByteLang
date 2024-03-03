import struct
from types import UnionType


class File:
    """Обёртка для работы с файлами"""

    @staticmethod
    def read(filepath: str):
        file = open(filepath)
        ret = file.read()
        file.close()
        return ret

    @staticmethod
    def save(filepath: str, data: str | bytes, mode: str):
        file = open(file=filepath, mode=mode)
        file.write(data)
        file.close()


class Bytes:
    """Упаковка и распаковка двоичных структур """

    class __DataType:
        def __init__(self, size: int, format_name: str):
            self.fmt_char = format_name
            self.size = size

    __types: dict[str, __DataType] = {
        "char": __DataType(1, "c"),
        "int8": __DataType(1, "b"),
        "uint8": __DataType(1, "B"),
        "bool": __DataType(1, "?"),
        "int16": __DataType(2, "h"),
        "uint16": __DataType(2, "H"),
        "int32": __DataType(4, "i"),
        "uint32": __DataType(4, "I"),
        "int64": __DataType(8, "q"),
        "uint64": __DataType(8, "Q"),
        "float": __DataType(4, "f"),
        "double": __DataType(8, "d"),
    }

    @classmethod
    def __translateTypeFormat(cls, _format: str) -> str:
        return "".join((
            cls.__types.get(fmt).fmt_char
            for fmt in _format.split(" ")
        ))

    @classmethod
    def __convertTypes(cls, _values: tuple) -> tuple:
        return tuple((
            bytes(val, encoding="utf-8") if isinstance(val, str) else val
            for val in _values
        ))

    @classmethod
    def __reverseConvertTypes(cls, _values: tuple):
        return tuple((
            str(val, encoding="utf-8") if isinstance(val, bytes) else val
            for val in _values
        ))

    @classmethod
    def pack(cls, _format: str, _values: tuple) -> bytes:
        return struct.pack(cls.__translateTypeFormat(_format), *cls.__convertTypes(_values))

    @classmethod
    def unpack(cls, _format: str, _data: bytes) -> tuple:
        return tuple(cls.__reverseConvertTypes(struct.unpack(cls.__translateTypeFormat(_format), _data)))


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

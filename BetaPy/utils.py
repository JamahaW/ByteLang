import struct


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

    # "string": "s"

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

    __packable = str | float | int

    @classmethod
    def pack(cls, _format: str, _values: list[__packable | list[__packable]]) -> bytes:
        formats = _format.split(" ")

        if len(formats) != len(_values):
            raise ValueError(f"formats must be equals values count")

        ret = bytes()

        for fmt, array in zip(formats, _values):
            array_length = 1
            string_mode = False

            if fmt.startswith("char"):
                array = bytes(array, encoding="utf-8")
                string_mode = True

            if fmt[-1] == "]":
                fmt, array_length = fmt.split("[")

                array_length = int(array_length[:-1])

                if array_length < len(array):
                    raise ValueError(f"unexpected array len: {array_length} - {array}")

                diff = array_length - len(array)

                ex = (0,) * diff

                if string_mode:
                    array += bytes(ex)
                else:
                    array.extend(ex)

            else:
                array = [array]

            if (datatype := cls.__types.get(fmt)) is None:
                raise ValueError(f"Invalid Format Key: {fmt}")

            if string_mode:
                ret += struct.pack(f"{array_length}s", array)

            else:
                ret += struct.pack(datatype.fmt_char * array_length, *array)

        return ret

    @classmethod
    def unpack(cls, _data: bytes, _format: str) -> list[__packable | list[__packable]]:
        pass


if __name__ == "__main__":
    data = Bytes.pack2("char[10] double[10]", [
        "abcd",
        [1/i for i in range(1, 10)]
    ])

    print(list(data))

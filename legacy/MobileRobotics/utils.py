import json
import math
import struct

import typez
from typez import Bytes as ByteTypes
from typez import Json
from typez import Path
from typez import StringList
from typez import StringPair


class Math:
    """
    Служебный класс математических вычислений
    """

    @staticmethod
    def digitsCount(number: int) -> int:
        """Возвращает количество цифр в числе"""
        if number == 0:
            return 1

        return int(math.log10(number)) + 1

    @staticmethod
    def inRange(x, _min, _max) -> bool:
        return _min <= x <= _max


class File:
    """
    Служебный класс операций с файлами
    """

    @staticmethod
    def getPath(file: typez.Path):
        """
        /folder/folder/file.txt -> /folder/folder/
        """
        return file.replace("\\", "/")[:file.rfind("/") + 1]

    @staticmethod
    def __load(file: Path, mode="r", encoding="1251"):
        if "b" in mode:
            return open(file, mode)

        return open(file, mode, encoding=encoding)

    @classmethod
    def saveBinary(cls, file: Path, content: bytes):
        cls.save(file, content, "wb")

    @classmethod
    def save(cls, file: Path, content, mode="w"):
        file = cls.__load(file, mode)
        file.write(content)
        file.close()

        return content

    @classmethod
    def saveJSON(cls, file: Path, data: Json):
        f = cls.__load(file, "w")
        json.dump(data, f)
        f.close()

    @classmethod
    def readJSON(cls, file: Path) -> Json:
        return json.loads(cls.read(file))

    @classmethod
    def readBinary(cls, file: Path) -> bytes:
        return bytes(cls.read(file, "rb"))

    @classmethod
    def read(cls, file: Path, mode="r") -> str | bytes:
        file = cls.__load(file, mode)
        content = file.read()
        file.close()

        return content

    class JsonUnpacker:
        """
        Чтение JSON в определённый класс
        """

        def __init__(self, data: Json, parsing_function=None):
            for field, value in data.items():
                if parsing_function is not None:
                    value = parsing_function(value)

                self.__dict__[field] = value

            self.__string = f"<{self.__class__} {self.__dict__}>"

        def __repr__(self):
            return self.__string


class String:
    """
    Служебный класс для строк
    """

    class Buffer:

        def __init__(self):
            self.message = ""

        def write(self, message: str, *, end="\n"):
            self.message += message + end
            return self

        def __repr__(self):
            return f"<StringBuffer: {len(self.message)}>"

        def __str__(self) -> str:
            return self.message

        def toString(self) -> str:
            return self.__str__()

    @staticmethod
    def fromList(data: list, *, separator="\n", name_format="%s", indent=0) -> str:
        buffer = ""

        indent_str = " " * indent

        for item in data:
            buffer += f"{indent_str}{(name_format % str(item))}{separator}"

        return buffer

    @staticmethod
    def indexedTable(data: list, begin_index: int = 0):
        buffer = ""

        offset = Math.digitsCount(len(data))

        for index, item in enumerate(data):
            buffer += f"{index + begin_index:>{offset}}: {item}\n"

        return buffer

    @classmethod
    def tableFromDict(cls, data: dict, *, name="", delimiter=" : ", separator="\n", indent=0):
        buffer = ""

        if name != "":
            buffer += f"[ {name} ]\n"

        name_len = cls.getMaxStringLen(list(data.keys()))

        indent_str = " " * indent

        for _name, value in data.items():
            buffer += f"{indent_str}{_name:<{name_len}}{delimiter}{value}{separator}"

        return buffer

    @staticmethod
    def tree(string, *, tabs=4, begin="[", end="]", sep=","):
        indent = 0
        result = ""
        offset = " " * tabs
        scope = True

        for char in string:
            wide = offset * indent

            if char == begin:
                result += char + "\n" + wide + offset
                indent += 1

            elif char == end:
                indent -= 1
                result += "\n" + (offset * indent) + char

            elif char == sep:
                if scope:
                    result += char + "\n" + wide

                else:
                    result += char

            else:
                if char in ("(", ")"):
                    scope ^= 1

                result += char

        return result

    @staticmethod
    def getMaxStringLen(data: StringList):
        if not len(data):
            return 0

        return len(max(data, key=lambda x: len(x)))

    @staticmethod
    def replaceWords(strings: StringList, old_word: str, new_word: str) -> StringList:
        result = StringList()

        for string in strings:
            words = string.split()
            words = [new_word if word == old_word else word for word in words]
            result.append(" ".join(words))

        return result

    @staticmethod
    def packHex(value, flag):
        return struct.pack(flag, value).hex()

    @staticmethod
    def showBytesArray(data: bytes) -> str:
        buffer = "{"
        l_data = list(data)

        for i in l_data:
            buffer += f"0x{i:0<2x}, "

        return buffer + "};\n"


class Bytes:
    __formatTranslator: dict[str, str] = {
        "char": "c", "int8": "b", "uint8": "B", "bool": "?", "int16": "h", "uint16": "H", "int32": "i", "uint32": "I", "int64": "q", "uint64": "Q", "float": "f", "string": "s"
    }

    __SizeTypes: dict[str, int] = {
        "char": 1, "int8": 1, "uint8": 1, "bool": 1, "int16": 2, "uint16": 2, "int32": 4, "uint32": 4, "int64": 8, "uint64": 8, "float": 4,
    }

    @classmethod
    def typeExist(cls, t: ByteTypes.Format):
        return t in cls.__formatTranslator.keys()

    @classmethod
    def getRange(cls, t: ByteTypes.Format) -> tuple[int, int]:
        size = cls.__SizeTypes[t]
        signed = t[0] != "u"

        abs_range = int(pow(2, 8 * size))
        half_range = abs_range // 2

        min_value = 0
        max_value = abs_range - 1

        if signed:
            min_value -= half_range
            max_value -= half_range

        return min_value, max_value

    @classmethod
    def valueInRange(cls, value: int, t: ByteTypes.Format) -> bool:
        _min, _max = cls.getRange(t)
        return Math.inRange(value, _min, _max)

    @classmethod
    def __checkValues(cls, _values: ByteTypes.FormatList) -> str:
        formats = ""

        for raw_key in _values:
            key_values = raw_key.split(" ")
            key = key_values[0]

            if key not in cls.__formatTranslator.keys():
                raise ValueError(f"unknown type: {key}")

            adder = ""
            ln = len(key_values)

            if ln > 2:
                raise ValueError(f"unexpected format: {raw_key}")

            if ln > 1 and key == "string":
                adder = key_values[1]

            key = cls.__formatTranslator[key] + adder

            formats += key

        return formats

    @classmethod
    def sizeof(cls, formatting: ByteTypes.FormatList, offset=0) -> int:
        for format_type in formatting:
            offset += cls.__SizeTypes[format_type]

        return offset

    @classmethod
    def unpack(cls, formatting: ByteTypes.FormatList, _data: bytes) -> ByteTypes.ValueList:
        return ByteTypes.ValueList(struct.unpack(cls.__checkValues(formatting), _data))

    @classmethod
    def pack(cls, _values: ByteTypes.PackList) -> bytes:
        result = bytes()

        for f, value in _values:
            result += struct.pack(cls.__checkValues([f]), value)

        return result


class Generate:

    @staticmethod
    def define(name: str, value: str = "", comment: str = "") -> str:
        if value:
            value = f"( {value} )"

        buffer = f"#define {name} {value}"

        if comment:
            buffer += f"  // {comment}"

        return buffer + "\n"

    @staticmethod
    def typedef(name: typez.Name, reference_type: typez.Name) -> str:
        return f"typedef {reference_type} {name};\n"

    @staticmethod
    def typedefFunction(name: typez.Name, return_type: typez.Name, signature: typez.StringList) -> str:
        return f"typedef {return_type} (*{name}) ({', '.join(signature)});\n"

    @staticmethod
    def fancyComment(text: str, *, length: int = 60, border: bool = False) -> str:
        buffer = ""

        def commentBar(size: int = length, end: str = "\n") -> str:
            return "//" + "/" * size + end

        text_off = (length - len(text)) // 2 - 4

        buffer += "\n"

        if border:
            buffer += commentBar()

        buffer += commentBar(text_off, end="   ") + f"{text.upper()}   " + commentBar(text_off)

        if border:
            buffer += commentBar()

        buffer += "\n"

        return buffer

    @staticmethod
    def enum(name: typez.Name, items: typez.StringList, *, values: typez.StringList = None, last_count=False, item_name_prefix="", item_upper=True, value_upper=True) -> str:
        buffer = ""

        buffer += f"enum {name} {{\n"

        offset = String.getMaxStringLen(items)

        for index, item in enumerate(items):
            val = "" if values is None else f" = {values[index]}"

            if item_upper:
                item = item.upper()

            if value_upper:
                val = val.upper()

            buffer += f"  {item_name_prefix}{item:<{offset}}{val},\n"

        if last_count:
            buffer += f"  {name}_COUNT\n"

        buffer += "};\n"

        return buffer

    @classmethod
    def function(cls, return_type: str, name: str, args: list[StringPair] = None, *, static=False, comment="", inline=False, const=False, name_prefix="", header=False) -> str:
        buffer = ""

        if inline:
            buffer += "inline "

        if static:
            buffer += "static "

        if const:
            buffer += "const "

        signature = ""

        if comment:
            comment = f"/* {comment} */"

        body = f";  {comment}" if header else f" {{ {comment} }}"

        if args is not None:
            for arg_type, arg_name in args:
                signature += f"{arg_type} {arg_name},"

        buffer += f"{return_type} {name_prefix}{name}({signature[:-1]}){body}\n"

        return buffer

    @classmethod
    def void_function_void(cls, name: str, *, static=False, comment="", inline=False, name_prefix="", header=False):
        return cls.function("void", name, None, static=static, comment=comment, inline=inline, name_prefix=name_prefix, header=header)

    @classmethod
    def array(cls, name: str, _type: str, data: list[str], *, static=False, each_line=False, indexed=True, name_prefix="", define_size=False, define_length=False) -> str:
        buffer = ""

        element_separator = " " if each_line else "\n"

        if static:
            buffer += "static "

        buffer += f"{_type} {name}[] {{{element_separator}"

        max_name_len = String.getMaxStringLen(list(data))

        if indexed:
            for index, el_name in enumerate(data):
                buffer += f"  {name_prefix}{el_name:<{max_name_len + 1}},  // {index}{element_separator}"

        else:
            for el_name in data:
                buffer += f"  {name_prefix}{el_name},{element_separator}"

        buffer += f"}};{element_separator}\n"

        if define_size:
            buffer += cls.define(f"{name}_SIZE", f"sizeof({name})")

        if define_length:
            buffer += cls.define(f"{name}_LENGTH", f"sizeof({name}) / sizeof({_type})")

        return buffer + "\n"

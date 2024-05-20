Path = str
Name = str

StringList = list[str]
StringSet = set[str]
StringDict = dict[str, str]
StringPair = tuple[str, str]

IntDict = dict[str, int]
IntList = list[int]
IntSet = set[int]

Size = int
ComPort = str
Json = dict[str, list | int | float | bool | str | dict]
CompiledProgram = bytes


class Bytes:
    Format = str
    FormatList = list[Format]
    Value = bool | int | str | float
    ValueList = list[Value]
    PackItem = tuple[Format, Value]
    PackList = list[PackItem]

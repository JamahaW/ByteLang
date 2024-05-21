import serial
import serial.tools.list_ports

SEND_TABLE = 0x10
LOAD_PROGRAM = 0x11
REMOVE_PROGRAM = 0x12
SEND_PROGRAMS_COUNT = 0x13
DELETE_PROGRAMS = 0x14

PROGRAM_SIZE = 17
PROGRAM_COUNT_AVAILABLE = 4
PROGRAM_TABLE_SIZE = PROGRAM_COUNT_AVAILABLE * PROGRAM_SIZE
PROGRAM_NAME_LEN = 12


# =============== ОТПРАВКА ===============

class SerialManager:
    """
    Менеджер отправки данных в указанный порт
    """
    BANNED_PORTS: set[str] = {"COM1"}

    def __init__(self, port, baud):
        self.serial = serial.Serial(port, baud)
        print(f"Подключено.\nПорт: {port}, Скорость: {baud}")

    def __send(self, commands: list[int]):
        self.serial.write(bytes(commands))

    def __send_one(self, value):
        self.__send([value])

    def __read(self, size):
        return self.serial.read(size)

    def __read_one(self):
        return self.__read(1)

    @classmethod
    def getPortList(cls):
        ports = list()

        for port in serial.tools.list_ports.comports():
            if (name := port.name) not in cls.BANNED_PORTS:
                ports.append(name)

        return ports

    def handle_ProgramGetTable(self):
        self.__send_one(SEND_TABLE)
        return self.__read(PROGRAM_TABLE_SIZE)

    def handle_ProgramUpload(self, program):
        self.__send([LOAD_PROGRAM] + program)

    def handle_ProgramRemove(self, index):
        self.__send([REMOVE_PROGRAM, index])

    def handle_ProgramGetCount(self):
        self.__send_one(SEND_PROGRAMS_COUNT)
        return self.__read_one()[0]

    def handle_ProgramClear(self):
        self.__send_one(DELETE_PROGRAMS)


class ControlManager:
    """
    Парсинг таблицы программ,

    автоматическая загрузка программ (выделение памяти и создание элемента таблицы)
    выборочное удаление программ
    """

    class TableProgram:
        def __init__(self, name, begin, size, index):
            self.name = name
            self.begin = begin
            self.size = size
            self.index = index

        def __repl__(self):
            return f"Program #{self.index}: '{self.name}' {self.begin}-{self.begin + self.size} ({self.size})"

        def show(self):
            return self.__repl__()

    FULL_INDICES = {i for i in range(PROGRAM_COUNT_AVAILABLE)}

    def __init__(self, sender):
        self.sender: SerialManager = sender
        self.programs: list[ControlManager.TableProgram | None] = [
                                                                      None] * PROGRAM_COUNT_AVAILABLE
        self.program_indices: dict[str, int] = dict()

    def upload(self, name: str, program: bytes):
        if name in self.program_indices.keys():
            self.delete(self.program_indices[name])

        programs_count = self.sender.handle_ProgramGetCount()

        if programs_count >= PROGRAM_COUNT_AVAILABLE:
            raise Exception(f"Загрузка {name} не была допущена")

        size = len(program)

        self.sender.handle_ProgramUpload(self.__generate_prog(name, 0, size))

    def delete(self, index: int):
        self.sender.handle_ProgramRemove(index)

    @staticmethod
    def __generate_prog(name: str, begin: int, size: int) -> list[int]:
        def packWord(val: int) -> list[int]:
            return [val & 0x00ff, val & 0xff00]

        res = [ord(name[i]) & 0xff for i in range(
            min(len(name), 12))]  # имя char[12]
        res += packWord(begin)  # начало uint16
        res += packWord(size)  # размер uint16
        res += [0]  # индекс = 0 uint8

        return res

    def unpack_programs(self):
        data = self.sender.handle_ProgramGetTable()

        for i in range(PROGRAM_COUNT_AVAILABLE):
            prog = data[i * PROGRAM_SIZE: (i + 1) * PROGRAM_SIZE]
            p = self.__unpack_program(prog)
            self.programs[i] = p
            self.program_indices[p.name] = p.index

        for i in self.programs:
            print(i.show())

    @staticmethod
    def __unpack_program(prog: bytes) -> TableProgram:
        offset = PROGRAM_NAME_LEN + 2

        name = bytes.decode(prog[:PROGRAM_NAME_LEN]).split('\0')[0]
        index = prog[-1]
        begin = prog[PROGRAM_NAME_LEN] + (prog[PROGRAM_NAME_LEN] << 8)
        size = prog[offset] + (prog[offset + 1] << 8)

        return ControlManager.TableProgram(name, begin, size, index)


# =============== ЛОГИКА ===============

def console(controller: ControlManager):
    print(f"Отправить команду на Arduino: load, del, data, stop")

    while True:
        args = input("> ").split()

        match args[0]:

            case "load":
                controller.upload(args[1], bytes(1))

            case "del":
                indices = int(args[1])
                controller.delete(indices)
                print(f"removed programs #{args}")

            case "data":
                controller.unpack_programs()
                print(controller.sender.handle_ProgramGetTable())

            case "stop":
                break

            case "clean":
                controller.sender.handle_ProgramClear()

            case _:
                print("Неверная команда.")


def main():
    ports_available = SerialManager.getPortList()
    print(f"Доступные порты: {ports_available}")

    sender = SerialManager(ports_available[0], 9600)
    controller = ControlManager(sender)

    console(controller)  # запуск консоли


if __name__ == "__main__":
    main()

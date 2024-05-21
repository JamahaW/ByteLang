import typez

import serial
import serial.tools.list_ports

import utils


class ProtocolManager:

    def __init__(self, init_config: str):
        self.__protocols = dict[str, types.SimpleNamespace]()
        self.__fill_protocols(utils.File.readJSON(init_config))

    def __fill_protocols(self, protocols: dict[str, list[str]], start_index=0):
        for name, values in protocols.items():
            start_index, data = self.__convert_indices(values, start_index)
            self.__protocols[name] = types.SimpleNamespace(**data)

    def get(self, protocol_name: str) -> types.SimpleNamespace:
        return self.__protocols.get(protocol_name)

    @staticmethod
    def __convert_indices(value: list[str], offset: int) -> tuple[int, dict[str, int]]:
        result = dict()

        for name in value:
            if (index := offset) > 255:
                raise IndexError(f"{name} index out of byte")

            result[name] = index
            offset += 1

        return offset, result


class SerialManager:
    """
    Менеджер отправки данных по порт
    """
    BANNED_PORTS: set[str] = {"COM1"}
    DEFAULT_BAUD = 9600

    def __init__(self, port, baud=DEFAULT_BAUD):
        self.serial = serial.Serial(port, baud)

        print(f"Подключено.\nПорт: {port}, Скорость: {baud}")

    def send(self, data: bytes):
        while self.serial.read() != b'\xff':
            pass
        self.serial.write(data)

    def sendByte(self, byte: int):
        self.send(bytes([byte]))

    def read(self, size) -> bytes:
        return self.serial.read(size)

    def readByte(self) -> int:
        return self.read(1)[0]

    @classmethod
    def getFirstPort(cls) -> str:
        if not (ports := cls.getPortList()):
            raise ValueError(f"No COM ports Available\n(blocked: {cls.BANNED_PORTS})")

        return ports[0]

    @classmethod
    def getPortList(cls) -> list[str]:
        ports = list()

        for port in serial.tools.list_ports.comports():
            if (name := port.name) not in cls.BANNED_PORTS:
                ports.append(name)

        return ports

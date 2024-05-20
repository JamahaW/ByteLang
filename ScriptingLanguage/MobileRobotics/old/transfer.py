import time

import serial
import serial.tools.list_ports

import typez
import utils
from typez import *


class SerialHandler:
    """
    Менеджер отправки данных по порту
    """

    __banned_ports: StringSet = None
    __protocol: IntDict = None

    baud: int = None
    final_code: int = None

    @staticmethod
    def __parseCommands(commands: StringList) -> IntDict:
        return {name: index for index, name in enumerate(commands)}

    @classmethod
    def init(cls, file: Path):
        config = utils.File.readJSON(file)
        cls.__protocol = cls.__parseCommands(config["commands"])
        cls.__banned_ports = StringSet(config["banned_ports"])
        cls.baud = config["baud"]
        cls.final_code = config["final_code"]

    @classmethod
    def generateNative(cls, output: Path, *, array_name="serCommands", func_prefix="serCMD_"):
        buffer = ""
        data = list(cls.__protocol.keys())

        for name in data:
            buffer += utils.Generate.void_function_void(name, static=True, name_prefix=func_prefix)

        buffer += "\n"

        buffer += utils.Generate.array(array_name, "function_t", data, static=True, define_length=True,
                                       define_size=True, name_prefix=func_prefix)

        buffer += f"\n"

        utils.File.save(output, buffer)

    @classmethod
    def getFirstPort(cls) -> ComPort:
        if not (ports := cls.getPortList()):
            raise ValueError(f"No COM ports Available\n(banned: {cls.__banned_ports})")

        return ports[0]

    @classmethod
    def getPortList(cls) -> list[ComPort]:
        ports = list[str]()

        for port in serial.tools.list_ports.comports():
            if (name := port.name) not in cls.__banned_ports:
                ports.append(name)

        return ports

    def __init__(self, port: ComPort):
        self.__serial = serial.Serial(port, self.baud)
        self.sendByte(0x01)  # отправить в порт байт, для определения платой

    def send(self, data: bytes):
        while self.readByte() != self.final_code:
            pass

        self.__serial.write(data)

    def sendByte(self, byte: int):
        self.send(bytes([byte]))

    def read(self, size) -> bytes:
        return self.__serial.read(size)

    def readByte(self) -> int:
        return self.read(1)[0]

    def getCode(self, command: str) -> int:
        return self.__protocol[command]

    def quit(self):
        self.__serial.close()


class CommunicationManager:
    """
    Занимается отправкой и принятием пакетов
    """

    """
    checker +
    program_get_table ~
    program_get_data ~
    program_erase +
    program_load ~
    robot_set_line_calibrate +
    robot_set_config ~
    robot_get_config ~
    robot_set_motor_pid +
    """

    def __init__(self, sender: SerialHandler):
        self.__sender = sender

    def __sendCommand(self, command: str, args: Bytes.PackList = None):
        """
        Отправить команду с данными (или без)
        """
        if args is None:
            args = Bytes.PackList()

        self.__sender.send(utils.Bytes.pack([("uint8", self.__sender.getCode(command)), *args]))

    def __readCommand(self, command: str, formatting: Bytes.FormatList) -> Bytes.ValueList:
        """
        Отправить запрос на получение данных
        """
        self.__sender.sendByte(self.__sender.getCode(command))
        return utils.Bytes.unpack(formatting, self.__sender.read(utils.Bytes.sizeof(formatting)))

    def checker(self, v3: float):
        """checker"""
        self.__sendCommand("checker", [("float", v3)])

    def setMotorPID(self, kp: float, ki: float, kd: float):
        """robot_set_motor_pid"""
        self.__sendCommand("robot_set_motor_pid", [("float", kp), ("float", ki), ("float", kd), ])

    def getProgramTable(self) -> object:
        """program_get_table"""
        pass

    def getProgramData(self, program_index: int) -> object:
        """program_get_data"""
        pass

    def eraseProgram(self, program_index: int):
        """program_erase"""
        self.__sendCommand("program_erase", [("uint8", program_index)])

    def loadProgram(self, program_item: int, program_data: bytes):
        """program_load"""

        data = utils.Bytes.pack(
            [("uint8", self.__sender.getCode("program_load")), ("uint8", program_item), ("uint16", len(program_data))])

        self.__sender.send(data + program_data)

    def setRobotLineCalib(self, sensor_index: int, dark_value: int, bright_value: int):
        """robot_set_line_calibrate"""
        self.__sendCommand("robot_set_line_calibrate",
                           [("uint8", sensor_index), ("uint16", dark_value), ("uint16", bright_value)])

    def setRobotConfig(self, config):
        """robot_set_config"""
        pass

    def getRobotConfig(self) -> object:
        """robot_get_config"""
        pass


class ConnectionHandler:
    """
    Менеджер подключения
    """

    def __init__(self):
        SerialHandler.init("../data/transfer/serial_config.json")
        # SerialHandler.generateNative("assets/data/uart_enum.txt")

        self.serialManager: SerialHandler | None = None
        self.communicationHandler: CommunicationManager | None = None

    def __test(self):
        time.sleep(2)

        data = bytes([5, 20, 0, 0, 0, 3, 1, 5, 1, 6, 1, 2, 5, 0, 0, 0, 0])

        self.communicationHandler.loadProgram(0, data)

    def __transmission(self):
        try:
            print("Началась передача")
            self.__test()

            print("передача завершена")
            self.serialManager.quit()

        except serial.SerialException as e:
            print(f"Отключено: {e}")

    def __connect(self, port: ComPort):
        try:
            self.serialManager = SerialHandler(port)
            self.communicationHandler = CommunicationManager(self.serialManager)

            print(f"Подключено: {port} ({self.serialManager.baud})")
            self.__transmission()

        except serial.SerialException as e:
            print(f"{e}\nНе удалось подключиться: {port}")

    def __searching(self, port: typez.ComPort):
        repeat_delay = 1.0

        while True:
            if port in (ports := SerialHandler.getPortList()):
                self.__connect(port)

                while port in SerialHandler.getPortList():
                    pass
            else:
                print(f"Не найдено: {port} ({ports})")
                time.sleep(repeat_delay)

    def run(self):
        port = SerialHandler.getFirstPort()

        try:
            self.__searching(port)

        except ValueError as e:
            print(f"{e}")

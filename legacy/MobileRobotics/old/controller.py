import device
import utils


class BasicController:
    """
    Служебный класс для работы отправки и приёма команд
    """
    __sender = None  # экземпляр класса SerialManager
    __protocolManager = None  # экземпляр менеджера протокола

    @classmethod
    def init(cls, sender: device.SerialManager, protocol_manager: device.ProtocolManager):
        """
        Для всех контроллеров будет общий менеджер протокола и порта
        """
        cls.__sender = sender
        cls.__protocolManager = protocol_manager

    def __init__(self, name: str):
        self._protocol = self.__protocolManager.get(name)

    def _sendCommand(self, code: int, args=None):
        """
        Отправить команду с данными (или без)
        """
        if args is None:
            args = list[utils.BytesLegacy.FormatType, utils.BytesLegacy.ValueType]()

        self.__sender.send(utils.BytesLegacy.pack([
            ("uint8", code),
            *args
        ]))

    def _readCommand(self, code: int, formatting: list[utils.BytesLegacy.FormatType]) -> list[utils.BytesLegacy.ValueType]:
        """
        Отправить запрос на получение данных
        """
        self.__sender.sendByte(code)
        return utils.BytesLegacy.unpack(formatting, self.__sender.read(utils.BytesLegacy.sizeof(formatting)))


class TesterController(BasicController):

    def __init__(self):
        super().__init__("tester")

    def show_value(self, value: int):
        self._sendCommand(self._protocol.show_value, ["int16", value])

    def show_float(self, value: float):
        self._sendCommand(self._protocol.show_value, ["float", value])

    def get_millis(self) -> int:
        return self._readCommand(self._protocol.get_millis, ["uint32"])[0]


class MotorController(BasicController):

    def __init__(self):
        super().__init__("pid")

    def set_pid(self, kp: float, ki: float, kd: float):
        self._sendCommand(self._protocol.set_pid, [("float", kp), ("float", ki), ("float", kd)])

    def set_speed(self, target_speed: float):
        self._sendCommand(self._protocol.set_speed, [("float", target_speed)])

    def get_speed(self) -> float:
        return self._readCommand(self._protocol.get_speed, ["float"])[0]

    def set_reverse(self, enable: bool):
        self._sendCommand(self._protocol.set_reverse, [("bool", enable)])

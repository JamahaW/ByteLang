import matplotlib.animation
import matplotlib.figure
import matplotlib.pyplot
import matplotlib.widgets
import serial
import serial.tools.list_ports

import utils


class MotorProtocol:
    SEND_PID = 1
    SET_TARGET_SPEED = 2
    GET_CURRENT_SPEED = 3
    SET_REVERSE = 4


class SerialManager:
    """
    Менеджер отправки данных по порт
    """
    BANNED_PORTS: set[str] = { "COM1" }
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
    def getPortList(cls):
        ports = list()
        
        for port in serial.tools.list_ports.comports():
            if (name := port.name) not in cls.BANNED_PORTS:
                ports.append(name)
        
        return ports


class MotorController:
    
    def __init__(self, sender: SerialManager):
        self.__sender = sender
        self.__last_target_speed = 0
    
    def set_pid(self, kp: float, ki: float, kd: float):
        self.__sender.send(utils.Bytes.pack([("uint8", MotorProtocol.SEND_PID), ("float", kp), ("float", ki), ("float", kd)]))
    
    def get_speed(self) -> float:
        self.__sender.sendByte(MotorProtocol.GET_CURRENT_SPEED)
        data = utils.Bytes.unpack(["float"], self.__sender.read(4))[0]
        
        return data
    
    def get_target(self) -> float:
        return self.__last_target_speed
    
    def set_speed(self, speed: float):
        self.__last_target_speed = speed
        self.__sender.send(utils.Bytes.pack([("uint8", MotorProtocol.SET_TARGET_SPEED), ("float", speed)]))
    
    def set_reverse(self, reverse: bool):
        self.__sender.send(utils.Bytes.pack([("uint8", MotorProtocol.SET_REVERSE), ("bool", reverse)]))


Vector2 = tuple[float, float]


def getDimension(pos: Vector2, size: Vector2):
    pos_x, pos_y = pos
    size_x, size_y = size
    return [pos_x - size_x / 2, 1.0 - (pos_y - size_y / 2), size_x, size_y]


class PlotterBase:
    
    def __init__(self):
        self._figure, self.__graph_axes = matplotlib.pyplot.subplots()
        self.__graph_axes.grid()
    
    def _setOffsets(self, left: float, right: float, top: float, bottom: float):
        self._figure.subplots_adjust(left=left, right=1.0 - right, top=1.0 - top, bottom=bottom)
    
    @staticmethod
    def _addButton(name: str, callback, pos: Vector2, size: Vector2 = (0.3, 0.075)):
        button_axes = matplotlib.pyplot.axes(getDimension(pos, size))
        button = matplotlib.widgets.Button(button_axes, name)
        button.on_clicked(callback)
        return button
    
    @staticmethod
    def _addSlider(name: str, pos: Vector2, _range: Vector2, *, size: Vector2 = (0.25, 0.03), _format: str = "%1.3f"):
        val_min, val_max = _range
        axes = matplotlib.pyplot.axes(getDimension(pos, size))
        slider = matplotlib.widgets.Slider(axes, label=name, valinit=0, valmin=val_min, valmax=val_max, valfmt=_format)
        return slider


class PlotterApp(PlotterBase):
    
    def __init__(self, controller: MotorController, end_values: int = 50):
        super().__init__()
        
        self._setOffsets(0.1, 0.5, 0.1, 0.1)
        
        self.__speed_slider = self._addSlider("S", (0.7, 0.2), (-1.5, 1.5))
        self.__set_speed_button = self._addButton("установить скорость", self.__onButton_send_speed, (0.7, 0.4))
        self.__stop_button = self._addButton("остановить", self.__onButton_stop, (0.7, 0.5))
        
        self.__p_slider = self._addSlider("P", (0.7, 0.65), (0, 1000))
        self.__i_slider = self._addSlider("I", (0.7, 0.70), (0, 1000))
        self.__d_slider = self._addSlider("D", (0.7, 0.75), (0, 10))
        self.__send_pid_button = self._addButton("Отправить", self.__onButton_send_pid, (0.7, 0.9))
        
        self.__controller = controller
        
        self.__current_speed = list[float]()
        self.__target_speed = list[float]()
        self.__ax = self._figure.add_subplot(111)
        self.__end_values = end_values
    
    def __onButton_send_speed(self, _):
        self.__controller.set_speed(self.__speed_slider.val)
    
    def __onButton_stop(self, _):
        self.__controller.set_speed(0)
    
    def __onButton_send_pid(self, _):
        p = self.__p_slider.val
        i = self.__i_slider.val
        d = self.__d_slider.val
        self.__controller.set_pid(p, i, d)
    
    def run(self):
        _ = matplotlib.animation.FuncAnimation(self._figure, self.animate, frames=500, interval=10)
        matplotlib.pyplot.show()
    
    def animate(self, _):
        self.__current_speed.append(self.__controller.get_speed())
        self.__current_speed = self.__current_speed[-self.__end_values:]
        
        self.__target_speed.append(self.__controller.get_target())
        self.__target_speed = self.__target_speed[-self.__end_values:]
        
        self.__ax.clear()
        self.configurePlot()
        self.__ax.plot(self.__current_speed)
        self.__ax.plot(self.__target_speed)
    
    def configurePlot(self):
        self.__ax.set_ylim([0, 2])
        self.__ax.set_xlim([0, self.__end_values])
        self.__ax.set_title("Скорость мотора")
        self.__ax.set_ylabel("об/сек")


def manual(controller: MotorController):
    app = PlotterApp(controller)
    app.run()


def main():
    sender = SerialManager(SerialManager.getPortList()[0])
    controller = MotorController(sender)
    
    manual(controller)


if __name__ == "__main__":
    main()

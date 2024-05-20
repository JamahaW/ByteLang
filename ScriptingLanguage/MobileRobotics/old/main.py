import device
import utils


def main():
    serial_settings = utils.File.readJSON("../assets/data/serial.json")
    device.SerialDevice.init(serial_settings)
    commands = device.SerialDevice.generateIndexedDict(serial_settings["commands"])
    device.SerialDevice.genereteNativeVM(commands, "../assets/data/serial_commands.txt")
    # ports = device.SerialDevice.getPortList()

    # if len(ports):
    #     target_port = ports[0]
    #     sender = device.SerialDevice(target_port)

    # else:
    #     print("Нет доступных портов")


if __name__ == "__main__":
    main()

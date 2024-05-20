"""
Описания конфигурации робота, его настроек и технических компонентов
"""

import utils
from typez import Json
from typez import Name
from typez import Path
from typez import StringDict
from typez import StringList
from typez import StringSet


class PinBase:
    """Базовый класс пина"""
    
    __propertyTranslations: StringDict = None
    
    @classmethod
    def init(cls, property_translations: StringDict):
        cls.__propertyTranslations = property_translations
    
    def __parseFlags(self) -> str:
        return " ".join([self.__propertyTranslations[flag] for flag in self.properties])
    
    def __init__(self, properties: StringList):
        self.properties = StringSet(properties)
        self.view = self.__parseFlags()


class PinReference(PinBase):
    """Пин, указанный в компоненте"""
    
    def __init__(self, properties: StringList, title: str):
        super().__init__(properties)
        self.title = title
    
    def __repr__(self):
        return f"<ref pin '{self.title}': {self.view}>"


class ArduinoPin(PinBase):
    """Параметры Пина Arduino"""
    
    def __init__(self, name: str, index: int, properties: StringList):
        super().__init__(properties)
        self.index = index
        self.name = name
    
    def __repr__(self):
        return f"<pin {self.name} - {self.index}: {self.view}>"


class ComponentReference:
    """Компонент робота"""
    
    @staticmethod
    def __parsePins(data: Json) -> dict[str, PinReference]:
        return { name: PinReference(pin_data["properties"], pin_data["title"]) for name, pin_data in data.items() }
    
    def __init__(self, data: Json):
        self.title = data["title"]
        self.hide = data.getLog("hide", False)
        self.max_count = data.getLog("max_count", 1)
        self.pins = self.__parsePins(data["pins"])
    
    def __repr__(self):
        return f"<component '{self.title}' show={self.hide} max={self.max_count}:{utils.String.fromDict(self.pins, separator=' ')}>"


class ComponentError(Exception):
    
    def __init__(self, message: str):
        super().__init__(f"Ошибка Компонента: {message}")


class ComponentNotExist(ComponentError):
    
    def __init__(self, component: Name):
        super().__init__(f"Указан неизвестный идентификатор: {component}")


class ComponentUnexpectedIndex(ComponentError):
    
    def __init__(self, component: Name, index: int):
        super().__init__(f"недействительный индекс {index} для компонента '{component}'")


class ComponentPinNotContain(ComponentError):
    
    def __init__(self, pin: Name, component: Name):
        super().__init__(f"'{component}'не содержит пин: {pin}")


class UnknownArduinoPin(ComponentError):
    
    def __init__(self, pin: Name):
        super().__init__(f"Пин {pin} не существует")


class ComponentPinInvalidProperties(ComponentError):
    
    def __init__(self, reference: PinReference, response: ArduinoPin):
        super().__init__(f"Пин {response.name}: '{response.view}' не соответствует свойствам '{reference.view}'")


class ComponentPinAlreadyUsing(ComponentError):
    
    def __init__(self, pin, behavior):
        super().__init__(f"Пин {pin} уже используется в {behavior}")


class RobotConfiguration:
    """Конфигурация робота"""
    
    """
    Метод превращения в байты
    параметры
    калибровка
    пид
    программы
    компоненты
    """
    
    @staticmethod
    def __parsePins(pins_config: Json) -> dict[str, ArduinoPin]:
        return { name: ArduinoPin(name, **pin_data) for name, pin_data in pins_config.items() }
    
    @staticmethod
    def __parseComponents(component_config: Json) -> dict[str, ComponentReference]:
        return { name: ComponentReference(data) for name, data in component_config.items() }
    
    @staticmethod
    def __getComponentIdentifier(component: Name, index: int, pin_name: Name) -> str:
        return f"{component}::{index}::{pin_name}"
    
    def __init__(self, component: Path, pins: Path, translation: Path):
        component_config = utils.File.readJSON(component)
        pins_config = utils.File.readJSON(pins)
        
        translation_json = utils.File.readJSON(translation)
        PinBase.init(translation_json["property"])
        
        self.__PINS = self.__parsePins(pins_config)
        self.__COMPONENTS = self.__parseComponents(component_config)
        
        self.__pin_behaviors: dict[str, str | None] | None = None
        self.__component_pins: dict[str, dict[int, dict[str, str | None]]] | None = None
        self.clear()
    
    def __checkPinExist(self, component: Name, pin_name: Name) -> PinReference:
        if (pin_reference := self.__COMPONENTS[component].pins.get(pin_name)) is None:
            raise ComponentPinNotContain(pin_name, component)
        
        return pin_reference
    
    def __checkComponentExist(self, component: Name):
        if component not in self.__COMPONENTS.keys():
            raise ComponentNotExist(component)
    
    def clearPin(self, component: Name, index: int, pin_name: Name):
        self.__checkComponentExist(component)
        _ = self.__checkPinExist(component, pin_name)
        
        if self.__component_pins[component].get(index) is None:
            raise ComponentUnexpectedIndex(component, index)
        
        pin = self.__component_pins[component][index][pin_name]
        self.__pin_behaviors[pin] = None
        self.__component_pins[component][index][pin_name] = None
    
    def setPin(self, component: Name, index: int, pin_name: Name, pin: str):
        
        if (behavior := self.__pin_behaviors.get(pin)) is not None:
            raise ComponentPinAlreadyUsing(pin, behavior)
        
        if (pin_arduino := self.__PINS.get(pin)) is None:
            raise UnknownArduinoPin(pin)
        
        self.__checkComponentExist(component)
        pin_reference = self.__checkPinExist(component, pin_name)
        
        if not pin_reference.properties.issubset(pin_arduino.properties):
            raise ComponentPinInvalidProperties(pin_reference, pin_arduino)
        
        self.__pin_behaviors[pin] = self.__getComponentIdentifier(component, index, pin_name)
        
        element = { pin_name: pin }
        
        if self.__component_pins.get(component) is None:
            self.__component_pins[component] = { 0: element }
        
        elif self.__component_pins[component].get(index) is None:
            self.__component_pins[component][index] = element
        
        else:
            self.__component_pins[component][index][pin_name] = pin
    
    def clear(self):
        self.__pin_behaviors = StringDict()
        self.__component_pins = dict[str, list[StringDict]]()
    
    def load(self, config: Path):
        self.clear()
        config_json = utils.File.readJSON(config)
        pins_config: dict[Name, list[StringDict]] = config_json["pins"]
        
        for component_name, component_list in pins_config.items():
            for index, component_data in enumerate(component_list):
                for pin_name, pin_identifier in component_data.items():
                    self.setPin(component_name, index, pin_name, pin_identifier)
    
    def save(self, file: Path):
        pass
    
    def test_show(self):
        print(utils.String.fromDict(self.__component_pins))
        print(utils.String.fromDict(self.__pin_behaviors))


def test():
    robot_config = RobotConfiguration("assets/data/robot/components.json", "assets/data/robot/pins.json", "assets/data/robot/ru.json")
    
    try:
        robot_config.load("assets/data/robot/configurations/test_platform.json")

    except ComponentError as e:
        print(e)

    else:
        robot_config.test_show()


if __name__ == "__main__":
    test()

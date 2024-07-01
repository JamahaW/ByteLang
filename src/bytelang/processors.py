from typing import Optional

from bytelang.registries import EnvironmentsRegistry
from bytelang.registries import PackageRegistry
from bytelang.registries import ProfileRegistry


class Compiler:
    """
    API byteLang
    Позволяет задать пути к пакетам инструкций, профилям, Окружениям
    Получить программу, ошибки, логи
    """

    def __init__(self) -> None:
        self.__packageRegistry = PackageRegistry("blp")
        self.__profileRegistry = ProfileRegistry("json")
        self.__environmentRegistry = EnvironmentsRegistry("json", self.__profileRegistry, self.__packageRegistry)

        # TODO остальные реестры

    def run(self, source_file: str) -> bool:
        """
        Скомпилировать исходный код bls в байткод программу
        :param source_file: Путь к исходному файлу
        :return Компиляция была завершена успешно (True)
        """
        pass

    def setEnvironmentsFolder(self, folder: str) -> None:
        """
        Указать путь к папке окружений
        :param folder:
        """
        self.__environmentRegistry.setFolder(folder)

    def setPackagesFolder(self, folder: str) -> None:
        """
        Указать путь к папке пакетов инструкций
        :param folder:
        """
        self.__packageRegistry.setFolder(folder)

    def setProfilesFolder(self, folder: str) -> None:
        """
        Указать путь к папке профилей
        :param folder:
        """
        self.__profileRegistry.setFolder(folder)

    def getProgram(self) -> Optional[bytes]:
        """
        Получить скомпилированный байткод.
        :return скомпилированный байткод. None Если программа не была скомпилирована
        """
        pass

    def getErrorsLog(self) -> Optional[str]:
        """
        Получить логи ошибок.
        :return лог ошибок или None, если ошибок не было
        """
        pass

    def getInfoLog(self) -> str:
        """
        Получить подробную информацию о компиляции
        """
        pass

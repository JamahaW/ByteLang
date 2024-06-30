from typing import Optional


class Compiler:
    """
    API byteLang
    Позволяет задать пути к пакетам инструкций, профилям, Окружениям
    Получить программу, ошибки, логи
    """

    def __init__(self) -> None:
        pass

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
        pass

    def setPackagesFolder(self, folder: str) -> None:
        """
        Указать путь к папке пакетов инструкций
        :param folder:
        """
        pass

    def setProfilesFolder(self, folder: str) -> None:
        """
        Указать путь к папке профилей
        :param folder:
        """
        pass

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

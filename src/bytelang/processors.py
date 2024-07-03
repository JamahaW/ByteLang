from __future__ import annotations

from os import PathLike
from typing import Optional

from bytelang.handlers import ErrorHandler
from bytelang.parsers import Parser
from bytelang.registries import EnvironmentsRegistry
from bytelang.registries import PackageRegistry
from bytelang.registries import PrimitiveTypeRegistry
from bytelang.registries import ProfileRegistry
from bytelang.tools import ReprTool


class Compiler:
    """API byteLang"""

    def __init__(self) -> None:
        self.__primitive_type_registry = PrimitiveTypeRegistry()
        self.__profile_registry = ProfileRegistry("json", self.__primitive_type_registry)
        self.__package_registry = PackageRegistry("blp", self.__primitive_type_registry)
        self.environment_registry = EnvironmentsRegistry("json", self.__profile_registry, self.__package_registry)
        # TODO остальные реестры

        self.__error_handler = ErrorHandler()
        self.__lexical_analyzer = Parser(self.__error_handler)

    def run(self, source_file: PathLike | str) -> bool:
        """
        Скомпилировать исходный код bls в байткод программу
        :param source_file: Путь к исходному файлу.
        :return Компиляция была завершена успешно (True)
        """

        with open(source_file) as f:
            statements = self.__lexical_analyzer.run(f)

            print(ReprTool.column(statements))

        # TODO доделать

        return self.__error_handler.success()

    def setPrimitivesFile(self, filepath: PathLike | str) -> None:
        """
        Указать путь к файлу настройки примитивных типов
        :param filepath:
        """
        self.__primitive_type_registry.setFile(filepath)

    def setEnvironmentsFolder(self, folder: PathLike | str) -> None:
        """
        Указать путь к папке окружений
        :param folder:
        """
        self.environment_registry.setFolder(folder)

    def setPackagesFolder(self, folder: PathLike | str) -> None:
        """
        Указать путь к папке пакетов инструкций
        :param folder:
        """
        self.__package_registry.setFolder(folder)

    def setProfilesFolder(self, folder: PathLike | str) -> None:
        """
        Указать путь к папке профилей
        :param folder:
        """
        self.__profile_registry.setFolder(folder)

    def getProgram(self) -> Optional[bytes]:
        """
        Получить скомпилированный байткод.
        :return скомпилированный байткод. None Если программа не была скомпилирована
        """

    def getErrorsLog(self) -> Optional[str]:
        """
        Получить логи ошибок.
        :return лог ошибок или None, если ошибок не было
        """
        if not self.__error_handler.success():
            return self.__error_handler.getLog()

    def getInfoLog(self) -> str:
        """
        Получить подробную информацию о компиляции
        """

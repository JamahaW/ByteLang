from __future__ import annotations

from os import PathLike
from typing import Optional

from bytelang.handlers import ErrorHandler
from bytelang.processors import CompileResult
from bytelang.processors import Compiler
from bytelang.registries import EnvironmentsRegistry
from bytelang.registries import PackageRegistry
from bytelang.registries import PrimitiveTypeRegistry
from bytelang.registries import ProfileRegistry


class ByteLang:
    """API byteLang"""

    # TODO декомпиляция
    # TODO Генератор кода виртуальной машины на основе окружения
    # TODO generic интерпретатор
    # TODO REPL режим

    def __init__(self) -> None:
        self.__primitive_type_registry = PrimitiveTypeRegistry()
        self.__profile_registry = ProfileRegistry("json", self.__primitive_type_registry)
        self.__package_registry = PackageRegistry("blp", self.__primitive_type_registry)
        self.__environment_registry = EnvironmentsRegistry("json", self.__profile_registry, self.__package_registry)
        self.__errors_handler = ErrorHandler()
        self.__compiler = Compiler(self.__errors_handler, self.__primitive_type_registry, self.__environment_registry)

    def compile(self, source_filepath: PathLike | str, bytecode_filepath: PathLike | str) -> Optional[CompileResult]:
        """Скомпилировать исходный код bls в байткод программу"""
        self.__errors_handler.reset()
        return self.__compiler.run(source_filepath, bytecode_filepath)

    def decompile(self, env: str, bytecode_filepath: PathLike | str, source_filepath: PathLike | str) -> None:
        """Декомпилировать байткод с данной средой ВМ и сгенерировать исходный код"""
        pass

    def setPrimitivesFile(self, filepath: PathLike | str) -> None:
        """Указать путь к файлу настройки примитивных типов"""
        self.__primitive_type_registry.setFile(filepath)

    def setEnvironmentsFolder(self, folder: PathLike | str) -> None:
        """Указать путь к папке окружений"""
        self.__environment_registry.setFolder(folder)

    def setPackagesFolder(self, folder: PathLike | str) -> None:
        """Указать путь к папке пакетов инструкций"""
        self.__package_registry.setFolder(folder)

    def setProfilesFolder(self, folder: PathLike | str) -> None:
        """Указать путь к папке профилей"""
        self.__profile_registry.setFolder(folder)

    def getErrorsLog(self) -> str:
        """Получить логи ошибок."""
        return self.__errors_handler.getLog()

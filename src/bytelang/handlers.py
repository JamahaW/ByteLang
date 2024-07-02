from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from bytelang.tools import ReprTool


class BasicErrorHandler(ABC):
    """Базовый обработчик сообщений ошибок"""

    def __init__(self):
        self.__failed = False
        """Был ли вызов записи ошибки"""

    def begin(self) -> None:
        """Подготовка к работе"""
        self.__failed = False

    def failed(self) -> bool:
        """
        Перед критическими действиями нужно проверить,
        что этапы выше были выполнены без ошибок
        """
        return self.__failed

    def getChild(self, name: str) -> BasicErrorHandler:
        """
        Получить дочерний обработчик ошибок от этого
        :param name:
        :return:
        """
        return ChildErrorHandler(name, self)

    def writeLineAt(self, line: str, index: int, message: str) -> None:
        self.write(f"{message} at {index} '{line.strip()}'")

    def write(self, message: str) -> None:
        """Добавить ошибку"""
        self.__failed = True
        self._appendMessage(message)

    @abstractmethod
    def _appendMessage(self, message: str) -> None:
        """Добавить сообщение. Для каждой реализации свой вариант"""


class ErrorHandler(BasicErrorHandler):
    """Основной обработчик ошибок"""

    def __init__(self) -> None:
        super().__init__()
        self.__messages = list[str]()
        """Набор сообщений ошибок"""

    def success(self) -> bool:
        """Нет ли ошибки"""
        return self.count() == 0

    def reset(self) -> None:
        """Очистить набор ошибок"""
        self.begin()
        self.__messages.clear()

    def _appendMessage(self, message: str) -> None:
        self.__messages.append(message)

    def count(self) -> int:
        return len(self.__messages)

    def getLog(self) -> str:
        return ReprTool.headed("errors", self.__messages)


class ChildErrorHandler(BasicErrorHandler):
    """Дочерний обработчик ошибок"""

    def __init__(self, name: str, parent: BasicErrorHandler) -> None:
        super().__init__()
        self.__name = name
        self.__parent = parent

    def _appendMessage(self, message: str) -> None:
        self.__parent.write(f"[{self.__name}]: {message}")

from __future__ import annotations

from .mini import Statement
from bytelang.tools import ReprTool


class ErrorHandler:

    def __init__(self, inst: object):
        self.__name = inst.__class__.__name__

        self.__messages = list[str]()
        self.__failed = False

    def reset(self):
        self.__messages.clear()
        self.begin()

    def begin(self) -> bool:
        ret = bool(self.__failed)
        self.__failed = False
        return ret

    def message(self, message: str) -> None:
        self.__messages.append(message)
        self.__failed = True

    def statement(self, error_name: str, statement: Statement) -> None:
        self.message(f"{statement.source_line.strip():32} at {statement.line:3} : [{error_name}]")

    def nameExist(self, statement: Statement, name: str) -> None:
        self.statement(f"Name '{name}' already Exist!", statement)

    def unknownName(self, name: str, statement: Statement) -> None:
        self.statement(f"Name {name} is Unknown!", statement)

    def invalidType(self, lexeme: str, expect_typename: str) -> None:
        self.message(f"cannot cast {lexeme} to {expect_typename}")

    def __needToSelectBase(self, content_name: str, statement: Statement) -> None:
        self.statement(f"Need to select {content_name}", statement)

    def platformNotSelected(self, statement: Statement) -> None:
        self.__needToSelectBase("platform", statement)

    def packageNotSelected(self, statement: Statement) -> None:
        self.__needToSelectBase("package", statement)

    def invalidArgCount(self, statement: Statement, need: int) -> None:
        self.statement(f"Invalid arg count for {statement.lexeme}. need {need} got ({len(statement.args)})", statement)

    def __getErrorCount(self) -> int:
        return len(self.__messages)

    def has(self) -> bool:
        return self.__getErrorCount() > 0

    def getLog(self) -> str:
        return f"{self.__name} has {self.__getErrorCount()} errors:\n{ReprTool.column(self.__messages, sep=' - ', begin=1)}"

from __future__ import annotations

from bytelang.mini import Statement


class ErrorHandler:

    def __init__(self, inst: object):
        self.name = inst.__class__.__name__

        self.__errors_messages = list[str]()

    def addErrorMessage(self, message: str) -> None:
        self.__errors_messages.append(message)

    def errorStatement(self, error_name: str, statement: Statement) -> None:
        self.addErrorMessage(f"{statement.source_line.strip():32} at {statement.line:3} : [{error_name}]")

    def __getErrorCount(self) -> int:
        return len(self.__errors_messages)

    def hasErrors(self) -> bool:
        return self.__getErrorCount() > 0

    def getErrors(self) -> str:
        messages = ''.join(
            map(
                (lambda m: f"\t{m}\n"),
                self.__errors_messages
            )
        )
        return f"{self.name} has {self.__getErrorCount()} errors:\n{messages}"

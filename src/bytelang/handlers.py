from __future__ import annotations

from .mini import Statement


class ErrorHandler:

    def __init__(self, inst: object):
        self.name = inst.__class__.__name__

        self.errors_messages = list[str]()

    def errorMessage(self, message: str) -> None:
        self.errors_messages.append(message)

    def errorStatement(self, error_name: str, statement: Statement) -> None:
        self.errorMessage(f"{statement.source_line.strip():32} at {statement.line:3} : [{error_name}]")

    def __getErrorCount(self) -> int:
        return len(self.errors_messages)

    def hasErrors(self) -> bool:
        return self.__getErrorCount() > 0

    def extendLog(self, inner: ErrorHandler) -> None:
        self.errors_messages.extend(inner.errors_messages)

    def getErrors(self) -> str:
        messages = ''.join(
            map(
                (lambda m: f"\t{m}\n"),
                self.errors_messages
            )
        )
        return f"{self.name} has {self.__getErrorCount()} errors:\n{messages}"

class ByteLangError(Exception):
    """Основное исключение модуля bytelang"""


class InterpreterError(ByteLangError):
    """Исключение интерпретатора"""

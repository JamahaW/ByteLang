from .handlers import ErrorHandler


class ByteLangError(Exception):
    pass


class ByteLangCompileError(ByteLangError):
    def __init__(self, error_handler: ErrorHandler):
        super().__init__(error_handler.getErrors())

class CompilationFailed(Exception):
    """
    Ошибка во время компиляции
    """
    pass


class LangInvalidSyntax(Exception):
    """
    Неверный синтаксис
    """
    pass


class MoshLangParseError(Exception):
    """
    Ошибка парсинга
    """
    pass

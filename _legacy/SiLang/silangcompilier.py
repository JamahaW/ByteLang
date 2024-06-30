from __future__ import annotations

"""
Это пример парсера рекурсивного спуска для следующей грамматики:

stmt ->  expr | E (epsilon)
expr -> term | term + expr | term - expr
term ->  fact | fact * term | fact / term
fact -> NUM | ( expr )
Где терминал символами являются символы NUM ( ) + * - /
Все остальные символы нон-терминал.
"""

import enum


class Token(enum.Enum):
    """Типы токенов"""

    END = enum.auto()
    NUMBER = enum.auto()
    PLUS = enum.auto()
    MINUS = enum.auto()
    STAR = enum.auto()
    SLASH = enum.auto
    LP = enum.auto()
    RP = enum.auto()
    UNKNOWN = enum.auto()


class TokenLexeme:
    """Носитель токена"""

    def __init__(self, token: Token, lexeme: str | None):
        self.token: Token = token
        self.lexeme: str | None = lexeme

    def __repr__(self):
        return f"<Token[{self.token}]: '{self.lexeme}'>"

    def copy(self) -> TokenLexeme:
        return TokenLexeme(self.token, self.lexeme)


class Tokenizer:
    __TOKEN_TABLE: dict[str, Token] = {
        "+": Token.PLUS,
        "-": Token.MINUS,
        "*": Token.STAR,
        "/": Token.SLASH,
        "(": Token.LP,
        ")": Token.RP
    }

    @classmethod
    def __tokenize(cls, source_code: str) -> list[TokenLexeme]:

        def __getToken(__char: str) -> TokenLexeme:
            ret: TokenLexeme = TokenLexeme(Token.END, None)

            if __char in "0123456789":
                ret.token = Token.NUMBER

            elif (tok := cls.__TOKEN_TABLE.get(__char)) is not None:
                ret.token = tok

            if ret.token != Token.END:
                ret.lexeme = __char

            return ret

        return [__getToken(char) for char in source_code]

    def __init__(self):
        self.__index: int = 0
        self.__tokens = None

    def load(self, code: str):
        self.__index = 0
        self.__tokens = self.__tokenize(code)

    def getNext(self) -> TokenLexeme | None:
        ret = self.__tokens[self.__index]

        if ret.token != Token.END:
            self.__index += 1

        return ret

    def decrementIndex(self):
        self.__index -= 1


class Parser:

    def __init__(self):
        self.__tokenizer: Tokenizer = Tokenizer()

    def getTokenizer(self) -> Tokenizer:
        return self.__tokenizer

    def calculate(self) -> int:
        return self.__statement(self.__tokenizer.getNext())

    def __fact(self, token: TokenLexeme) -> int:
        ret: int = 0
        temp_token: TokenLexeme = token.copy()

        match temp_token.token:
            case Token.NUMBER:
                ret = int(token.lexeme)

            case Token.LP:
                temp_token = self.__tokenizer.getNext()
                ret = self.__expression(temp_token)
                self.__tokenizer.getNext()  # Считываем закрывающуюся скобку

        return ret

    def __terminal(self, token: TokenLexeme) -> int:
        temp_token: TokenLexeme = token.copy()
        ret: int = 0

        if temp_token.token in (Token.LP, Token.NUMBER):
            ret = self.__fact(temp_token)
            temp_token = self.__tokenizer.getNext()

            match temp_token.token:
                case Token.STAR:
                    temp_token = self.__tokenizer.getNext()
                    ret *= self.__terminal(temp_token)

                case Token.SLASH:
                    temp_token = self.__tokenizer.getNext()
                    ret /= self.__terminal(temp_token)

                case Token.PLUS | Token.RP | Token.MINUS:
                    self.__tokenizer.decrementIndex()

        return ret

    def __expression(self, token: TokenLexeme) -> int:
        temp_token: TokenLexeme = token.copy()
        ret: int = 0

        if temp_token.token in (Token.LP, Token.NUMBER):
            ret = self.__terminal(temp_token)
            temp_token = self.__tokenizer.getNext()

            match temp_token.token:
                case Token.PLUS:
                    temp_token = self.__tokenizer.getNext()
                    ret += self.__expression(temp_token)

                case Token.MINUS:
                    temp_token = self.__tokenizer.getNext()
                    ret -= self.__expression(temp_token)

                case Token.RP:
                    self.__tokenizer.decrementIndex()

        return ret

    def __statement(self, token: TokenLexeme) -> int:
        ret: int = 0

        match token.token:
            case Token.LP | Token.NUMBER:
                ret = self.__expression(token)

        return ret

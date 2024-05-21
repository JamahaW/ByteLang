import enum
import re

import errors
import utils


class TokenType(enum.Enum):
    UNKNOWN = enum.auto()
    KEYWORD = enum.auto()
    DELIMITER = enum.auto()
    NAME = enum.auto()
    NUMBER = enum.auto()
    OPERATOR = enum.auto()


TokenList = list[tuple[TokenType, str]]
IdentifierSet = set[str]


class Keywords:
    # создать объект
    VARIABLE = "var"  # создать переменную
    FUNCTION = "func"  # создать и объявить функцию
    # управление блоком
    RETURN = "return"  # выйти из функции
    BREAK = "break"  # перейти в конец блока
    CONTINUE = "continue"  # перейти в начало блока
    # создать блок
    LOOP = "loop"  # вечный цикл
    WHILE = "while"  # цикл с условием
    FOR = "for"  # итерируемый цикл
    IF = "if"  # если
    ELIF = "elif"  # иначе если
    ELSE = "else"  # иначе


class Operators:
    ASSIGNMENT = "="
    EQUALS = "=="
    GREATER = ">"
    LESS = "<"
    NOT_EQUALS = "!="
    NOT_GREATER = "<="
    NOT_LESS = ">="
    NOT = "!"
    OR = "||"
    AND = "&&"
    INCREMENT = "++"
    DECREMENT = "--"
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    ASSIGNMENT_ADD = "+="
    ASSIGNMENT_SUB = "-="
    ASSIGNMENT_MUL = "*="
    ASSIGNMENT_DIV = "/="


class Delimiters:
    BLOCK_OPEN = "{"
    BLOCK_CLOSE = "}"
    BRACKETS_OPEN = "("
    BRACKETS_CLOSE = ")"
    SEPARATOR_ARG = ","
    SEPARATOR_COMMAND = ";"


class Tokenizer:
    keywords = None
    operators = None
    delimiters = None
    
    TOKEN_PATTERNS = [(r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.NAME), (r'[-+]?\d+', TokenType.NUMBER), (r'#.*', None), (r'\s+', None), (r'.', TokenType.UNKNOWN)]
    
    @classmethod
    def Init(cls):
        cls.keywords = [Keywords.VARIABLE, Keywords.FUNCTION, Keywords.RETURN, Keywords.BREAK, Keywords.CONTINUE, Keywords.LOOP, Keywords.WHILE, Keywords.FOR, Keywords.IF, Keywords.ELIF,
            Keywords.ELSE]
        
        cls.operators = [Operators.ASSIGNMENT, Operators.EQUALS, Operators.GREATER, Operators.LESS, Operators.NOT_EQUALS, Operators.NOT_GREATER, Operators.NOT_LESS, Operators.NOT, Operators.OR,
            Operators.AND, Operators.ADD, Operators.SUB, Operators.MUL, Operators.DIV, ]
        
        cls.delimiters = [Delimiters.BLOCK_OPEN, Delimiters.BLOCK_CLOSE, Delimiters.BRACKETS_OPEN, Delimiters.BRACKETS_CLOSE, Delimiters.SEPARATOR_ARG, Delimiters.SEPARATOR_COMMAND]
    
    @classmethod
    def process(cls, code):
        tokens = list()
        
        while code:
            match = None
            
            for pattern, token_type in cls.TOKEN_PATTERNS:
                match = re.compile(pattern).match(code)
                
                if match:
                    value = match.group(0)
                    
                    if token_type is not None:
                        for types, set_type in ((cls.keywords, TokenType.KEYWORD), (cls.operators, TokenType.OPERATOR), (cls.delimiters, TokenType.DELIMITER)):
                            if value in types:
                                token_type = set_type
                                break
                        
                        if token_type == TokenType.UNKNOWN:
                            raise ValueError(f"Invalid syntax: {code}")
                        
                        tokens.append((token_type, value))
                    break
            
            code = code[match.end():]
        
        return tokens


class Statements(enum.Enum):
    EXPRESSION_COMPARE = enum.auto()  # ... (A > B) { }
    EXPRESSION_COMPARE_ASSIGNMENT = enum.auto()  # X = (A == B)
    EXPRESSION_CALCULATE_ASSIGNMENT = enum.auto()  # X = A + B
    GETTER_COMMAND = enum.auto()
    
    CONTROL_BREAK = enum.auto()
    CONTROL_CONTINUE = enum.auto()
    CONTROL_RETURN = enum.auto()
    
    BLOCK_LOOP = enum.auto()
    BLOCK_WHILE = enum.auto()
    BLOCK_FOR = enum.auto()
    BLOCK_IF = enum.auto()
    BLOCK_ELIF = enum.auto()
    BLOCK_ELSE = enum.auto()
    
    CALL_COMMAND = enum.auto()
    CALL_FUNCTION = enum.auto()


class CommandArgument:
    
    def __init__(self, value: dict[str, str | int]):
        self.name: str = value["name"]
        self.type: str = value["type"]
        
        if self.type not in ("int", "enum", "args"):
            raise Exception(f"invalid arg '{self.name}' type: {self.type}")
        
        self.default: int | None = value.get("default")
        self.min: int = value.get("min", -30000)
        self.max: int = value.get("max", 30000)
        self.allowed_values: list[str] | None = value.get("allowed_values")
        
        self.__string_cache: str = self.__generateStringCache()
    
    def __generateStringCache(self) -> str:
        buffer = f"<arg '{self.name}': {self.type}"
        
        if self.allowed_values is not None and self.type == "int":
            values = "|".join(self.allowed_values)
            buffer += f"<{values}>"
        
        if self.default is not None:
            buffer += f" = {self.default}"
        
        if self.type == "int":
            buffer += f":[{self.min}..{self.max}]"
        
        if self.type == "enum":
            values = " | ".join(self.allowed_values)
            buffer += f" :[ {values} ]"
        
        return buffer + ">"
    
    def __repr__(self):
        return self.__string_cache
    
    def getLimits(self) -> tuple[int, int]:
        return self.min, self.max


class CommandWrapper:
    
    def __init__(self, name: str, data: dict):
        self.name = name
        self.args = [CommandArgument(__value) for __value in data["args"]]
        self.description = data["description"]
        self.type = data["type"]
    
    def __repr__(self):
        return f"<command '{self.name}'-{self.type} args: {self.args}>"


class CommandWords:
    # названия команд
    EXIT = "exit"
    WAIT = "wait"
    PRINT = "print"
    SERVO = "set_servo"
    TURN = "turn"
    TURN_CROSS = "turn_cross"
    RIDE = "ride"
    LINE = "line"
    GET_TIME = "get_time"
    GET_LINE = "get_line"
    GET_DIST = "get_dist"
    # типы команд
    GETTER = "getter"
    SETTER = "setter"
    # типы аргументов
    INTEGER = "int"
    ENUM = "enum"
    ARGS = "args"
    # допустимые значения
    CONST = "const"
    VARIABLE = "var"
    # перечисление
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    CENTER = "CENTER"
    DISTANCE = "DIST"
    TO_WALL = "WALL"
    TO_CROSS = "CROSS"
    ON_TIMER = "TIME"
    
    enum_items = { LEFT, RIGHT, CENTER, DISTANCE, TO_WALL, TO_CROSS, ON_TIMER }


class StatementUnit:
    
    def __init__(self, statement: Statements, args: None | list[str | object]):
        self.statement = statement
        self.args = args
    
    def __repr__(self):
        return f"<statement '{self.statement}': {self.args}>"


StatementList = list[StatementUnit]


class ProgramVariable:
    variableSize = 2
    
    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value
    
    def __repr__(self):
        return f"<variable: '{self.name}' = {self.value}>"


class ProgramFunction:
    
    def __init__(self, name: str, statements: list[StatementUnit]):
        self.name = name
        self.statements = statements
    
    def __repr__(self):
        return f"<function '{self.name}': {self.statements}>"


class Objectevizer:
    """
    Преобразует выражение в объектное представление
    """
    
    __singleKeywordTransform = {
        Keywords.BREAK: Statements.CONTROL_BREAK, Keywords.CONTINUE: Statements.CONTROL_CONTINUE
        }
    
    @staticmethod
    def __getTokenValues(tokens: TokenList) -> list[str]:
        return [__token for _, __token in tokens]
    
    def __init__(self, commands: dict[str, CommandWrapper]):
        self.__commands = commands
        
        self.__variable_identifiers = IdentifierSet()
        self.__function_identifiers = IdentifierSet()
        self.__command_identifiers = self.__commands.keys()
    
    def addVariable(self, name: str):
        self.__variable_identifiers.add(name)
    
    def addFunction(self, name: str):
        self.__function_identifiers.add(name)
    
    def getVariables(self):
        return self.__variable_identifiers
    
    def getFunctions(self):
        return self.__function_identifiers
    
    def __name_variable(self, name: str, tokens: TokenList) -> tuple[StatementUnit, int]:
        pass
    
    def __name_function(self, function_name: str, tokens: TokenList) -> tuple[StatementUnit, int]:
        other_tokens, token_count = Parser.getTokensStatement(tokens)
        token_types = self.__getTokenValues(other_tokens)
        
        if token_types != [Delimiters.BRACKETS_OPEN, Delimiters.BRACKETS_CLOSE]:
            raise errors.MoshLangParseError(f"invalid Function Call: {function_name}, {other_tokens}")
        
        return StatementUnit(Statements.CALL_FUNCTION, [function_name]), token_count + 2
    
    @staticmethod
    def __name_command_merge_args(args: list[tuple[str, str | int]], defaults_args: list[CommandArgument]):
        
        defaults = [(CommandWords.CONST, i.default) for i in defaults_args]
        
        ln = len(args)
        if ln < defaults.count((CommandWords.CONST, None)):
            raise ValueError("Недостаточно аргументов")
        
        merged_list = args + defaults[ln:]
        
        if len(merged_list) > len(defaults):
            raise Exception(f"слишком много аргументов: {args}, {defaults}")
        
        return merged_list
    
    def __name_command(self, name: str, tokens: TokenList) -> tuple[StatementUnit, int]:
        current_command: CommandWrapper = self.__commands[name]
        
        if current_command.type == CommandWords.GETTER:
            raise errors.MoshLangParseError(f"Cannot use {current_command.type} at this")
        
        checked_tokens, token_count = Parser.getTokensStatement(tokens)
        arg_tokens, _ = Parser.getTokensBlock(checked_tokens, begin=Delimiters.BRACKETS_OPEN, end=Delimiters.BRACKETS_CLOSE)
        args_values: list = Parser.getArguments(arg_tokens)
        
        if current_command.args[0].type != CommandWords.ARGS:
            args_values = self.__name_command_merge_args(args_values, current_command.args)
            
            for (arg_type, arg_value), reference_arg in zip(args_values, current_command.args):
                reference_arg: CommandArgument
                
                if reference_arg.type != CommandWords.ENUM:
                    if arg_type not in reference_arg.allowed_values:
                        raise errors.MoshLangParseError(f"unsupported type: {arg_type} in {reference_arg}")
                    
                    if arg_type == CommandWords.CONST:
                        min_value, max_value = reference_arg.getLimits()
                        
                        if arg_value < min_value or arg_value > max_value:
                            raise errors.MoshLangParseError(f"const value {arg_value} out of allowed arg range {reference_arg}")
                
                else:
                    if arg_value not in reference_arg.allowed_values:
                        raise errors.MoshLangParseError(f"invalid ENUM value: {arg_value} in arg: {reference_arg}")
        else:
            for arg_type, arg_value in args_values:
                if arg_type == CommandWords.ENUM:
                    raise errors.MoshLangParseError(f"Illegal arg type: {arg_type, arg_value}")
        
        return StatementUnit(Statements.CALL_COMMAND, [name] + args_values), token_count + 2
    
    def __name(self, name: str, tokens: TokenList) -> tuple[StatementUnit, int]:
        if name in self.__variable_identifiers:
            return self.__name_variable(name, tokens)
        
        if name in self.__function_identifiers:
            return self.__name_function(name, tokens)
        
        if name in self.__commands.keys():
            return self.__name_command(name, tokens)
        
        raise errors.MoshLangParseError(f"Unknown identifier {name}")
    
    def __keyword_control(self, keyword: str, tokens: TokenList) -> tuple[StatementUnit, int]:
        checked, count = Parser.getTokensStatement(tokens)
        token_value = None
        
        if count == 1:
            token_type, token_value = checked[0]
            
            if token_type != TokenType.NAME:
                raise errors.MoshLangParseError(f"not a block identifier: {token_value}")
        
        elif count > 1:
            raise errors.MoshLangParseError(f"unexpected tokens: {checked}")
        
        return StatementUnit(self.__singleKeywordTransform[keyword], token_value), 2 + count
    
    @staticmethod
    def __keyword_return(tokens: TokenList) -> tuple[StatementUnit, int]:
        checked, count = Parser.getTokensStatement(tokens)
        if count != 0:
            raise errors.MoshLangParseError(f"unexpected tokens: {checked}")
        
        return StatementUnit(Statements.CONTROL_RETURN, None), 2
    
    def __keyword_block_loop(self, tokens: TokenList) -> tuple[StatementUnit, int]:
        block_tokens, count = Parser.getTokensBlock(tokens)
        statements: list[StatementUnit] = self.parseStatements(block_tokens)
        
        return StatementUnit(Statements.BLOCK_LOOP, statements), count + 3
    
    def __keyword_block(self, keyword: str, tokens: TokenList) -> tuple[StatementUnit, int]:
        expression, exp_count = Parser.getTokensBlock(tokens, begin=Delimiters.BRACKETS_OPEN, end=Delimiters.BRACKETS_CLOSE)
        block_tokens, count = Parser.getTokensBlock(tokens[exp_count:])
        statements: list[StatementUnit] = self.parseStatements(block_tokens)
        
        return StatementUnit(Statements.BLOCK_LOOP, statements), count + 3
    
    def __keyword(self, keyword: str, tokens: TokenList) -> tuple[StatementUnit, int]:
        match keyword:
            case Keywords.RETURN:
                return self.__keyword_return(tokens)
            
            case Keywords.BREAK | Keywords.CONTINUE:
                return self.__keyword_control(keyword, tokens)
            
            case Keywords.LOOP:
                return self.__keyword_block_loop(tokens)
            
            case Keywords.WHILE:
                return self.__keyword_block(keyword, tokens)
            
            case _:
                raise errors.MoshLangParseError(f"invalid keyword: {keyword}")
    
    def __process(self, tokens: TokenList) -> tuple[StatementUnit, int]:
        (token_type, token_value), *other_tokens = tokens
        
        match token_type:
            case TokenType.NAME:
                return self.__name(token_value, other_tokens)
            
            case TokenType.KEYWORD:
                return self.__keyword(token_value, other_tokens)
            
            case _:
                raise errors.MoshLangParseError(f"invalid token {token_value}")
    
    def parseStatements(self, tokens: TokenList) -> StatementList:
        index = 0
        statements = list()
        
        while index < len(tokens):
            state, used = self.__process(tokens[index:])
            statements.append(state)
            index += used
        
        return statements


class Parser:
    """
    Получить из токенов переменные и функции с объективизированными выражениями
    """
    __globalTokens: set[tuple[TokenType, str]] = { (TokenType.KEYWORD, Keywords.VARIABLE), (TokenType.KEYWORD, Keywords.FUNCTION) }
    
    __variableTokenPatterns: dict[int, TokenList] = {
        3: [(TokenType.NAME, None), (TokenType.OPERATOR, Operators.ASSIGNMENT), (TokenType.NUMBER, None), ], 1: [(TokenType.NAME, None), ]
        }
    
    @staticmethod
    def getTokensStatement(tokens: TokenList, separator=(TokenType.DELIMITER, Delimiters.SEPARATOR_COMMAND)) -> tuple[TokenList, int]:
        checked_tokens = TokenList()
        
        for token in tokens:
            checked_tokens.append(token)
            
            if token == separator:
                break
        
        if checked_tokens[-1] != separator:
            raise errors.MoshLangParseError(f"Missing {separator} at end")
        
        checked_tokens = checked_tokens[:-1]
        
        return checked_tokens, len(checked_tokens)
    
    @staticmethod
    def getTokensBlock(tokens: TokenList, *, begin=Delimiters.BLOCK_OPEN, end=Delimiters.BLOCK_CLOSE) -> tuple[TokenList, int]:
        checked_tokens = TokenList()
        
        scope_sum = {
            (TokenType.DELIMITER, begin): 1, (TokenType.DELIMITER, end): -1
            }
        scopes = 0
        
        for token in tokens:
            delta = scope_sum.get(token)
            
            if delta is not None:
                scopes += scope_sum[token]
            
            checked_tokens.append(token)
            
            if scopes == 0:
                break
        
        if scopes != 0:
            raise errors.MoshLangParseError(f"Block not closed: {checked_tokens}")
        
        checked_tokens = checked_tokens[1:-1]
        
        return checked_tokens, len(checked_tokens)
    
    @staticmethod
    def getArguments(tokens: TokenList, separator=Delimiters.SEPARATOR_ARG):
        args = list()
        separator_flag = False
        
        for token_type, token_value in tokens:
            
            if separator_flag:
                if token_type != TokenType.DELIMITER:
                    raise errors.MoshLangParseError(f"invalid token: {token_value}")
            
            separator_flag ^= 1
            
            match token_type:
                case TokenType.NUMBER:
                    args.append((CommandWords.CONST, int(token_value)))
                
                case TokenType.NAME:
                    if token_value in CommandWords.enum_items:
                        args.append((CommandWords.ENUM, token_value))
                        continue
                    
                    args.append((CommandWords.VARIABLE, token_value))
                
                case TokenType.DELIMITER:
                    if token_value != separator:
                        raise errors.MoshLangParseError(f"Invalid symbol: {token_value}")
                
                case _:
                    raise errors.MoshLangParseError(f"invalid token: {token_value}")
        
        return args
    
    def __init__(self, commands_settings):
        commands = { __name: CommandWrapper(__name, __value) for __name, __value in commands_settings.items() }
        self.__objectivizer = Objectevizer(commands)
        
        self.__variable_objects = set[ProgramVariable]()
        self.__function_objects = set[ProgramFunction]()
        
        self.__keywordProcessTable = {
            Keywords.VARIABLE: self.__declareVariable, Keywords.FUNCTION: self.__declareFunction
            }
    
    def __declareVariable(self, tokens: TokenList) -> int:
        checked_tokens, token_count = self.getTokensStatement(tokens)
        pattern = self.__variableTokenPatterns.get(token_count)
        
        if pattern is None:
            raise errors.MoshLangParseError(f"invalid: {checked_tokens}")
        
        for (checked_token, checked_value), (pattern_token, pattern_value) in zip(checked_tokens, pattern):
            if checked_token != pattern_token:
                raise errors.MoshLangParseError(f"invalid token: {checked_token} ({pattern_token})")
            
            if pattern_value is not None and checked_value != pattern_value:
                raise errors.MoshLangParseError(f"invalid value: {checked_value} ({pattern_value})")
        
        variable_name = checked_tokens[0][1]
        variable_value = checked_tokens[2][1] if token_count == 3 else 0
        
        self.__variable_objects.add(ProgramVariable(variable_name, variable_value))
        self.__objectivizer.addVariable(variable_name)
        
        return token_count + 2
    
    def __declareFunction(self, tokens: TokenList) -> int:
        (name_token, name_value), *function_tokens = tokens
        
        if name_token != TokenType.NAME:
            raise errors.MoshLangParseError(f"invalid: {name_token = }")
        
        block_tokens, token_count = self.getTokensBlock(function_tokens)
        
        self.__objectivizer.addFunction(name_value)
        statements = self.__objectivizer.parseStatements(block_tokens)
        self.__function_objects.add(ProgramFunction(name_value, statements))
        
        return token_count + 4
    
    def __parseKeyword(self, keyword: str, tokens: TokenList) -> int:
        if (processor := self.__keywordProcessTable.get(keyword)) is None:
            raise errors.MoshLangParseError(f"invalid: {keyword = }")
        
        return processor(tokens)
    
    def process(self, tokens: TokenList):
        token_index = 0
        
        while token_index < len(tokens):
            token = tokens[token_index]
            
            if token not in self.__globalTokens:
                raise errors.MoshLangParseError(f"Parse Err: {token}, AT: {token_index}")
            
            _, token_value = token
            token_index += self.__parseKeyword(token_value, tokens[token_index + 1:])
    
    def getVariables(self) -> tuple[set[ProgramVariable], IdentifierSet]:
        return self.__variable_objects, self.__objectivizer.getVariables()
    
    def getFunctions(self) -> tuple[set[ProgramFunction], IdentifierSet]:
        return self.__function_objects, self.__objectivizer.getFunctions()


def main():
    # 1. считать файл MOSHLANG
    code = utils.File.read("../assets/test/main.msl")
    lang_settings = utils.File.readJSON("../assets/data/mosh_lang.json")
    
    # 2. токенизировать - Tokenizer
    Tokenizer.Init()
    tokens = Tokenizer.process(code)
    
    # 3. получить переменные и функции
    parser = Parser(lang_settings["commands"])
    parser.process(tokens)
    variable_objects, variable_identifiers = parser.getVariables()
    function_objects, function_identifiers = parser.getFunctions()
    
    print(utils.String.tree(utils.String.fromList(list(function_objects))))
    print(utils.String.fromList(list(variable_objects)))  # 4. объективизировать токены в функциях
    
    # 5.
    
    # вернуть файл BYTELANG


main()

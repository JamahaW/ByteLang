from . import utils
from .data import Package, Platform, ContextManager
from .errors import ByteLangError
from .lex import StatementType, Statement


class ByteLangCompiler:
    """Компилятор"""

    def __init__(self):
        self.COMMENT_CHAR = ';'
        self.DIRECTIVE_CHAR = '.'
        self.MARK_CHAR = ':'

        self.packages = ContextManager(Package)
        self.platforms = ContextManager(Platform)

    def tokenize(self, source) -> list[Statement]:
        buffer = list()
        source_lines = source.split("\n")

        for index, line in enumerate(source_lines):
            if (line_no_comment := line.split(self.COMMENT_CHAR)[0].strip()) != "":
                lexeme, *args = line_no_comment.split()

                _type = None

                if lexeme[-1] == self.MARK_CHAR:
                    _type = StatementType.MARK
                    lexeme = lexeme[:-1]

                elif lexeme[0] == self.DIRECTIVE_CHAR:
                    lexeme = lexeme[1:]
                    _type = StatementType.DIRECTIVE

                elif lexeme in self.packages.used.INSTRUCTIONS.keys():  # command exists
                    _type = StatementType.INSTRUCTION

                else:
                    raise ByteLangError(f"Invalid Statement: '{lexeme}' at Line {index} '{line}'")

                buffer.append(Statement(_type, lexeme, args, index + 1))

        return buffer

    def parse(self, statements: list[Statement]):
        pass

    def execute(self, input_path: str, output_path: str):
        if self.packages.used is None:
            raise ByteLangError("need to select package")

        if self.platforms.used is None:
            raise ByteLangError("need to select platform")

        source = utils.File.read(input_path)

        tokens = self.tokenize(source)

        print(tokens)

        program = bytes()

        utils.File.saveBinary(output_path, program)

import unittest

from bytelang import Lexer
from bytelang import Parser
from bytelang._ast import *


class ParserTestCase(unittest.TestCase):
    """Базовый класс для тестов парсера"""

    def _create_parser(self, source: str) -> Optional[Parser]:
        """Создать парсер из исходного кода"""
        lexer = Lexer("test", source)
        lexer.process()
        tokens = lexer.tokens()

        if tokens is None:
            print("Lexer errors:")
            for error in lexer.errors():
                print(error)
            return None

        return Parser(tokens)

    def _assert_no_errors(self, parser: Parser):
        """Убедиться, что нет ошибок парсинга"""
        errors = parser.errors()
        if errors:
            for error in errors:
                print(f"Parser error: {error.message} at {error.token}")
        self.assertEqual(len(errors), 0, "Ожидалось отсутствие ошибок парсинга")

    def _assert_has_errors(self, parser: Parser):
        """Убедиться, что есть ошибки парсинга"""
        self.assertGreater(len(parser.errors()), 0, "Ожидались ошибки парсинга")

    def _assert_is_instance(self, node, expected_type, message=""):
        """Проверить тип узла с информативным сообщением"""
        self.assertIsNotNone(node, f"Узел не должен быть None: {message}")
        self.assertIsInstance(node, expected_type,
                              f"Ожидался тип {expected_type.__name__}, получен {type(node).__name__}: {message}")
        return node


class TestParserBasic(ParserTestCase):
    """Тесты базовых методов парсера"""

    def test_identifier(self):
        """Тест парсинга идентификатора"""
        parser = self._create_parser("test")
        self.assertIsNotNone(parser)

        identifier = parser.identifier()
        self._assert_is_instance(identifier, Identifier, "identifier")
        self.assertEqual(identifier.id, "test")
        self._assert_no_errors(parser)

    def test_identifier_empty(self):
        """Тест парсинга идентификатора из пустого ввода"""
        parser = self._create_parser("")
        self.assertIsNotNone(parser)

        identifier = parser.identifier()
        self.assertIsNone(identifier)
        self._assert_has_errors(parser)

    def test_integer_literals(self):
        """Тест парсинга целочисленных литералов"""
        test_cases = [
            ("123", 123, "десятичный"),
            ("0xFF", 0xFF, "шестнадцатеричный"),
            ("0b1010", 0b1010, "двоичный"),
        ]

        for source, expected, desc in test_cases:
            with self.subTest(f"Целочисленный литерал: {desc}"):
                parser = self._create_parser(source)
                self.assertIsNotNone(parser)

                literal = parser.integer_literal()
                self._assert_is_instance(literal, IntegerLiteral, f"integer literal {desc}")
                self.assertEqual(literal.value, expected)
                self._assert_no_errors(parser)

    def test_string_literal(self):
        """Тест парсинга строкового литерала"""
        parser = self._create_parser('"hello world"')
        self.assertIsNotNone(parser)

        literal = parser.string_literal()
        self._assert_is_instance(literal, StringLiteral, "string literal")
        self.assertEqual(literal.value, "hello world")
        self._assert_no_errors(parser)

    def test_name_parsing(self):
        """Тест парсинга имен"""
        test_cases = [
            ("x", ["x"], "простое имя"),
            ("math.add", ["math", "add"], "имя с точкой"),
            ("a.b.c", ["a", "b", "c"], "имя с несколькими точками"),
        ]

        for source, expected_chain, desc in test_cases:
            with self.subTest(f"Имя: {desc}"):
                parser = self._create_parser(source)
                self.assertIsNotNone(parser)

                name = parser.name()
                self._assert_is_instance(name, Name, f"name {desc}")

                # Собираем цепочку идентификаторов
                chain = []
                current = name
                while current:
                    chain.append(current.identifier.id)
                    current = current.inner

                self.assertEqual(chain, expected_chain)
                self._assert_no_errors(parser)


class TestParserTypes(ParserTestCase):
    """Тесты парсинга типов"""

    def test_pure_type(self):
        """Тест парсинга чистого типа"""
        parser = self._create_parser("i32")
        self.assertIsNotNone(parser)

        type_node = parser.type()
        self._assert_is_instance(type_node, PureType, "pure type")
        self.assertEqual(type_node.name.identifier.id, "i32")
        self._assert_no_errors(parser)

    def test_pointer_type(self):
        """Тест парсинга указателя"""
        parser = self._create_parser("*i32")
        self.assertIsNotNone(parser)

        type_node = parser.type()
        self._assert_is_instance(type_node, PointerType, "pointer type")
        self._assert_is_instance(type_node.type, PureType, "inner type of pointer")
        self.assertEqual(type_node.type.name.identifier.id, "i32")
        self._assert_no_errors(parser)

    def test_array_type(self):
        """Тест парсинга массива"""
        parser = self._create_parser("[10]i32")
        self.assertIsNotNone(parser)

        type_node = parser.type()
        self._assert_is_instance(type_node, ArrayType, "array type")
        self.assertEqual(type_node.size.value, 10)
        self._assert_is_instance(type_node.type, PureType, "array element type")
        self.assertEqual(type_node.type.name.identifier.id, "i32")
        self._assert_no_errors(parser)

    def test_slice_type(self):
        """Тест парсинга среза"""
        parser = self._create_parser("[]u8")
        self.assertIsNotNone(parser)

        type_node = parser.type()
        self._assert_is_instance(type_node, SliceType, "slice type")
        self._assert_is_instance(type_node.type, PureType, "slice element type")
        self.assertEqual(type_node.type.name.identifier.id, "u8")
        self._assert_no_errors(parser)

    def test_function_signature_type(self):
        """Тест парсинга сигнатуры функции"""
        parser = self._create_parser("(x: i32, y: i32) i32")
        self.assertIsNotNone(parser)

        type_node = parser.type()
        self._assert_is_instance(type_node, FunctionSignatureType, "function signature type")

        signature = type_node.function_signature
        self._assert_is_instance(signature, FunctionSignature, "function signature")

        # Проверяем аргументы
        self.assertEqual(len(signature.arguments), 2)

        arg1 = signature.arguments[0]
        self._assert_is_instance(arg1, Field, "first argument")
        self.assertEqual(arg1.identifier.id, "x")
        self._assert_is_instance(arg1.type, PureType, "first argument type")
        self.assertEqual(arg1.type.name.identifier.id, "i32")

        arg2 = signature.arguments[1]
        self._assert_is_instance(arg2, Field, "second argument")
        self.assertEqual(arg2.identifier.id, "y")
        self._assert_is_instance(arg2.type, PureType, "second argument type")
        self.assertEqual(arg2.type.name.identifier.id, "i32")

        # Проверяем возвращаемый тип
        self._assert_is_instance(signature.return_type, PureType, "return type")
        self.assertEqual(signature.return_type.name.identifier.id, "i32")

        self._assert_no_errors(parser)


class TestParserExpressions(ParserTestCase):
    """Тесты парсинга выражений"""

    def test_address_take(self):
        """Тест взятия адреса"""
        parser = self._create_parser("&x")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_is_instance(expr, AddressTake, "address take")
        self._assert_is_instance(expr.name, Name, "name in address take")
        self.assertEqual(expr.name.identifier.id, "x")
        self._assert_no_errors(parser)

    def test_list_literal(self):
        """Тест парсинга спискового литерала"""
        parser = self._create_parser("{1, 2, 3}")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_is_instance(expr, ListLiteral, "list literal")
        self.assertEqual(len(expr.values), 3)

        # Проверяем значения
        for i, value in enumerate(expr.values, 1):
            self._assert_is_instance(value, IntegerLiteral, f"list element {i}")
            self.assertEqual(value.value, i)

        self._assert_no_errors(parser)

    def test_function_call_expression(self):
        """Тест парсинга вызова функции как выражения"""
        parser = self._create_parser("add(1, 2)")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_is_instance(expr, FunctionCallValue, "function call value")

        call = expr.function_call
        self._assert_is_instance(call, FunctionCall, "function call")
        self.assertEqual(call.name.identifier.id, "add")
        self.assertEqual(len(call.arguments), 2)

        # Проверяем аргументы
        for i, arg in enumerate(call.arguments, 1):
            self._assert_is_instance(arg, IntegerLiteral, f"argument {i}")
            self.assertEqual(arg.value, i)

        self._assert_no_errors(parser)


class TestParserStatements(ParserTestCase):
    """Тесты парсинга утверждений"""

    def test_return_statements(self):
        """Тест парсинга return"""
        test_cases = [
            ("return", None, "без значения"),
            ("return 42", 42, "со значением"),
        ]

        for source, expected_value, desc in test_cases:
            with self.subTest(f"Return: {desc}"):
                parser = self._create_parser(source)
                self.assertIsNotNone(parser)

                stmt = parser.statement()
                self._assert_is_instance(stmt, Return, f"return statement {desc}")

                if expected_value is None:
                    self.assertIsNone(stmt.returns)
                else:
                    self._assert_is_instance(stmt.returns, IntegerLiteral, "return value")
                    self.assertEqual(stmt.returns.value, expected_value)

                self._assert_no_errors(parser)

    def test_assign_statement(self):
        """Тест парсинга присваивания"""
        parser = self._create_parser("x = 10")
        self.assertIsNotNone(parser)

        stmt = parser.statement()
        self._assert_is_instance(stmt, Assign, "assign statement")

        self._assert_is_instance(stmt.name, Name, "assign target name")
        self.assertEqual(stmt.name.identifier.id, "x")

        self._assert_is_instance(stmt.expression, IntegerLiteral, "assign value")
        self.assertEqual(stmt.expression.value, 10)

        self._assert_no_errors(parser)

    def test_function_call_statement(self):
        """Тест парсинга вызова функции как утверждения"""
        parser = self._create_parser('print("hello")')
        self.assertIsNotNone(parser)

        stmt = parser.statement()
        self._assert_is_instance(stmt, FunctionCallStatement, "function call statement")

        call = stmt.function_call
        self._assert_is_instance(call, FunctionCall, "function call")
        self.assertEqual(call.name.identifier.id, "print")
        self.assertEqual(len(call.arguments), 1)

        arg = call.arguments[0]
        self._assert_is_instance(arg, StringLiteral, "argument")
        self.assertEqual(arg.value, "hello")

        self._assert_no_errors(parser)


class TestParserDeclarations(ParserTestCase):
    """Тесты парсинга объявлений"""

    def test_variable_declaration(self):
        """Тест объявления переменной"""
        parser = self._create_parser("var x: i32 = 10")
        self.assertIsNotNone(parser)

        decl = parser.declaration()
        self._assert_is_instance(decl, VariableDeclaration, "variable declaration")

        variable = decl.variable
        self._assert_is_instance(variable, Variable, "variable")

        field = variable.field
        self._assert_is_instance(field, Field, "field")
        self.assertEqual(field.identifier.id, "x")

        self._assert_is_instance(field.type, PureType, "field type")
        self.assertEqual(field.type.name.identifier.id, "i32")

        self._assert_is_instance(variable.expression, IntegerLiteral, "initial value")
        self.assertEqual(variable.expression.value, 10)

        self._assert_no_errors(parser)

    def test_symbol_declaration(self):
        """Тест объявления символа"""
        parser = self._create_parser("def PI = 3.14")
        self.assertIsNotNone(parser)

        decl = parser.declaration()
        self._assert_is_instance(decl, SymbolDeclaration, "symbol declaration")

        symbol = decl.symbol
        self._assert_is_instance(symbol, Symbol, "symbol")
        self.assertEqual(symbol.identifier.id, "PI")

        self._assert_is_instance(symbol.expression, RealLiteral, "symbol value")
        # Для float нужно сравнивать с float
        self.assertAlmostEqual(symbol.expression.value, 3.14, places=2)

        self._assert_no_errors(parser)

    def test_public_declaration(self):
        """Тест публичного объявления"""
        parser = self._create_parser("pub var x: i32 = 10")
        self.assertIsNotNone(parser)

        decl = parser.declaration()
        self._assert_is_instance(decl, PublicDeclaration, "public declaration")

        inner = decl.inner
        self._assert_is_instance(inner, VariableDeclaration, "inner variable declaration")

        variable = inner.variable
        self._assert_is_instance(variable, Variable, "variable in public declaration")
        self.assertEqual(variable.field.identifier.id, "x")

        self._assert_no_errors(parser)


class TestParserIntegration(ParserTestCase):
    """Интеграционные тесты парсера"""

    def test_simple_module(self):
        """Тест парсинга простого модуля"""
        source = """
var x: i32 = 10
def PI = 3.14
pub var y: i32 = 20
"""
        parser = self._create_parser(source)
        self.assertIsNotNone(parser)

        module = parser.module()
        self._assert_is_instance(module, Module, "module")

        # Проверяем количество объявлений
        self.assertEqual(len(module.declarations), 3)

        # Проверяем типы объявлений
        decl1 = module.declarations[0]
        self._assert_is_instance(decl1, VariableDeclaration, "first declaration")

        decl2 = module.declarations[1]
        self._assert_is_instance(decl2, SymbolDeclaration, "second declaration")

        decl3 = module.declarations[2]
        self._assert_is_instance(decl3, PublicDeclaration, "third declaration")

        self._assert_no_errors(parser)

    def test_complex_expression(self):
        """Тест парсинга сложного выражения"""
        parser = self._create_parser('{1, &x, "test"}')
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_is_instance(expr, ListLiteral, "complex list literal")
        self.assertEqual(len(expr.values), 3)

        # Проверяем элементы списка
        elem1 = expr.values[0]
        self._assert_is_instance(elem1, IntegerLiteral, "first element")
        self.assertEqual(elem1.value, 1)

        elem2 = expr.values[1]
        self._assert_is_instance(elem2, AddressTake, "second element")
        self.assertEqual(elem2.name.identifier.id, "x")

        elem3 = expr.values[2]
        self._assert_is_instance(elem3, StringLiteral, "third element")
        self.assertEqual(elem3.value, "test")

        self._assert_no_errors(parser)


class TestParserErrorCases(ParserTestCase):
    """Тесты обработки ошибок"""

    def test_missing_semicolon(self):
        """Тест обработки пропущенного токена"""
        parser = self._create_parser("var x i32 = 10")  # Пропущено ':'
        self.assertIsNotNone(parser)

        decl = parser.declaration()
        self.assertIsNone(decl)
        self._assert_has_errors(parser)

    def test_invalid_type(self):
        """Тест обработки невалидного типа"""
        parser = self._create_parser("var x: * = 10")  # Неполный тип указателя
        self.assertIsNotNone(parser)

        decl = parser.declaration()
        self.assertIsNone(decl)
        self._assert_has_errors(parser)

    def test_missing_expression(self):
        """Тест обработки пропущенного выражения"""
        parser = self._create_parser("var x: i32 =")  # Нет значения
        self.assertIsNotNone(parser)

        decl = parser.declaration()
        self.assertIsNone(decl)
        self._assert_has_errors(parser)


def run_all_tests():
    """Запустить все тесты с детальным выводом"""
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    # Для запуска конкретного теста: python -m unittest test_parser.TestParserBasic.test_identifier
    # Для запуска всех тестов: python -m unittest test_parser
    unittest.main(verbosity=2)

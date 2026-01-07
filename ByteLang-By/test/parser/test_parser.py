import unittest
from typing import Optional, Sequence, Type

from bytelang import Lexer
from bytelang import Parser
from bytelang._ast import *
from bytelang._token import TokenType


class ParserTestBase(unittest.TestCase):
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

    def _assert_node_type(self, node, expected_type: Type, message: str = ""):
        """Проверить тип узла с информативным сообщением"""
        self.assertIsNotNone(node, f"Узел не должен быть None: {message}")
        self.assertIsInstance(node, expected_type,
                              f"Ожидался тип {expected_type.__name__}, получен {type(node).__name__}: {message}")
        return node

    def _assert_identifier(self, identifier: Identifier, expected_id: str, message: str = ""):
        """Проверить идентификатор"""
        self._assert_node_type(identifier, Identifier, message)
        self.assertEqual(identifier.id, expected_id, f"Идентификатор должен быть '{expected_id}': {message}")

    def _assert_name(self, name: Name, expected_chain: list[str], message: str = ""):
        """Проверить имя (возможно с точками)"""
        self._assert_node_type(name, Name, message)

        chain = []
        current = name
        while current:
            chain.append(current.identifier.id)
            current = current.inner

        self.assertEqual(chain, expected_chain, f"Цепочка имени не совпадает: {message}")


class TestParserLiterals(ParserTestBase):
    """Тесты парсинга литералов"""

    def test_integer_literals(self):
        """Тест парсинга целочисленных литералов"""
        test_cases = [
            ("123", 123, "десятичный"),
            ("0xFF", 0xFF, "шестнадцатеричный"),
            ("0b1010", 0b1010, "двоичный"),
            ("'A'", ord('A'), "символьный"),
        ]

        for source, expected, desc in test_cases:
            with self.subTest(f"Целочисленный литерал: {desc}"):
                parser = self._create_parser(source)
                self.assertIsNotNone(parser)

                expr = parser.expression()
                self._assert_node_type(expr, IntegerLiteral, f"integer literal {desc}")
                self.assertEqual(expr.value, expected)
                self._assert_no_errors(parser)

    def test_real_literals(self):
        """Тест парсинга вещественных литералов"""
        test_cases = [
            ("3.14", 3.14, "обычный"),
            ("2.5e10", 2.5e10, "экспоненциальный"),
            ("-1.5", -1.5, "отрицательный"),
        ]

        for source, expected, desc in test_cases:
            with self.subTest(f"Вещественный литерал: {desc}"):
                parser = self._create_parser(source)
                self.assertIsNotNone(parser)

                expr = parser.expression()
                self._assert_node_type(expr, RealLiteral, f"real literal {desc}")
                self.assertAlmostEqual(expr.value, expected, places=5)
                self._assert_no_errors(parser)

    def test_string_literal(self):
        """Тест парсинга строкового литерала"""
        parser = self._create_parser('"hello world"')
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, StringLiteral, "string literal")
        self.assertEqual(expr.value, "hello world")
        self._assert_no_errors(parser)

    def test_list_literal(self):
        """Тест парсинга спискового литерала"""
        parser = self._create_parser('{1, 2.5, "test"}')
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, ListLiteral, "list literal")

        self.assertEqual(len(expr.values), 3)
        self._assert_node_type(expr.values[0], IntegerLiteral, "first element")
        self._assert_node_type(expr.values[1], RealLiteral, "second element")
        self._assert_node_type(expr.values[2], StringLiteral, "third element")

        self._assert_no_errors(parser)

    def test_undefined_literal(self):
        """Тест парсинга undefined"""
        parser = self._create_parser("undefined")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, UndefinedValue, "undefined literal")
        self._assert_no_errors(parser)


class TestParserNames(ParserTestBase):
    """Тесты парсинга имен"""

    def test_simple_name(self):
        """Тест парсинга простого имени"""
        parser = self._create_parser("x")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_name(expr, ["x"], "simple name")
        self._assert_no_errors(parser)

    def test_dotted_name(self):
        """Тест парсинга имени с точками"""
        test_cases = [
            ("math.add", ["math", "add"], "две части"),
            ("a.b.c", ["a", "b", "c"], "три части"),
            ("std.io.print", ["std", "io", "print"], "много частей"),
        ]

        for source, expected_chain, desc in test_cases:
            with self.subTest(f"Имя с точками: {desc}"):
                parser = self._create_parser(source)
                self.assertIsNotNone(parser)

                expr = parser.expression()
                self._assert_name(expr, expected_chain, desc)
                self._assert_no_errors(parser)


class TestParserTypeExpressions(ParserTestBase):
    """Тесты парсинга выражений-типов"""

    def test_pointer_type(self):
        """Тест парсинга указателя"""
        parser = self._create_parser("*u8")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, StarOperator, "pointer type")

        # Проверяем внутренний тип
        self._assert_name(expr.type, ["u8"], "pointer target type")
        self._assert_no_errors(parser)

    def test_array_type(self):
        """Тест парсинга массива"""
        parser = self._create_parser("[10]i32")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, ArrayType, "array type")

        # Проверяем размер
        self._assert_node_type(expr.size, IntegerLiteral, "array size")
        self.assertEqual(expr.size.value, 10)

        # Проверяем тип элементов
        self._assert_name(expr.item_type, ["i32"], "array element type")
        self._assert_no_errors(parser)

    def test_slice_type(self):
        """Тест парсинга среза"""
        parser = self._create_parser("[]u8")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, SliceType, "slice type")

        # Проверяем тип элементов
        self._assert_name(expr.item_type, ["u8"], "slice element type")
        self._assert_no_errors(parser)

    def test_struct_type(self):
        """Тест парсинга структуры"""
        source = "struct { x: i32, y: i32 }"
        parser = self._create_parser(source)
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, StructType, "struct type")

        # Проверяем поля структуры
        self.assertEqual(len(expr.declarations), 2)

        # Первое поле
        field1 = expr.declarations[0]
        self._assert_node_type(field1, Field, "first field")
        self._assert_identifier(field1.identifier, "x", "field name x")
        self._assert_name(field1.type, ["i32"], "field type i32")

        # Второе поле
        field2 = expr.declarations[1]
        self._assert_node_type(field2, Field, "second field")
        self._assert_identifier(field2.identifier, "y", "field name y")

        self._assert_no_errors(parser)

    def test_function_signature(self):
        """Тест парсинга сигнатуры функции"""
        parser = self._create_parser("(x: i32, y: i32) i32")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, FunctionSignature, "function signature")

        # Проверяем аргументы
        self.assertEqual(len(expr.arguments), 2)

        arg1 = expr.arguments[0]
        self._assert_identifier(arg1.identifier, "x", "first argument name")
        self._assert_name(arg1.type, ["i32"], "first argument type")

        arg2 = expr.arguments[1]
        self._assert_identifier(arg2.identifier, "y", "second argument name")
        self._assert_name(arg2.type, ["i32"], "second argument type")

        # Проверяем возвращаемый тип
        self._assert_name(expr.return_type, ["i32"], "return type")
        self._assert_no_errors(parser)

    def test_function_type(self):
        """Тест парсинга типа функции"""
        source = """
fn(x: i32, y: i32) i32 {
    return x
}
"""
        parser = self._create_parser(source)
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, FunctionType, "function type")

        # Проверяем сигнатуру
        self._assert_node_type(expr.function_signature, FunctionSignature, "function signature")

        # Проверяем операторы
        self.assertEqual(len(expr.statements), 1)
        self._assert_node_type(expr.statements[0], Return, "return statement")

        self._assert_no_errors(parser)


class TestParserFunctionCalls(ParserTestBase):
    """Тесты парсинга вызовов функций"""

    def test_function_call_no_args(self):
        """Тест вызова функции без аргументов"""
        parser = self._create_parser("print()")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, FunctionCall, "function call")

        self._assert_name(expr.name, ["print"], "function name")
        self.assertEqual(len(expr.arguments), 0)
        self._assert_no_errors(parser)

    def test_function_call_with_args(self):
        """Тест вызова функции с аргументами"""
        parser = self._create_parser('add(1, 2.5, "test")')
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, FunctionCall, "function call")

        self._assert_name(expr.name, ["add"], "function name")

        # Проверяем аргументы
        self.assertEqual(len(expr.arguments), 3)
        self._assert_node_type(expr.arguments[0], IntegerLiteral, "first argument")
        self._assert_node_type(expr.arguments[1], RealLiteral, "second argument")
        self._assert_node_type(expr.arguments[2], StringLiteral, "third argument")

        self._assert_no_errors(parser)

    def test_nested_function_call(self):
        """Тест вложенного вызова функции"""
        parser = self._create_parser("foo(bar(1), 2)")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, FunctionCall, "outer function call")

        self._assert_name(expr.name, ["foo"], "outer function name")
        self.assertEqual(len(expr.arguments), 2)

        # Первый аргумент - тоже вызов функции
        arg1 = expr.arguments[0]
        self._assert_node_type(arg1, FunctionCall, "nested function call")
        self._assert_name(arg1.name, ["bar"], "nested function name")

        self._assert_no_errors(parser)

    def test_address_take(self):
        """Тест взятия адреса"""
        parser = self._create_parser("&x")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, AddressTake, "address take")

        self._assert_name(expr.name, ["x"], "address target")
        self._assert_no_errors(parser)


class TestParserStatements(ParserTestBase):
    """Тесты парсинга операторов"""

    def test_symbol_statement(self):
        """Тест оператора определения символа"""
        parser = self._create_parser("def PI = 3.14")
        self.assertIsNotNone(parser)

        stmt = parser.statement()
        self._assert_node_type(stmt, Symbol, "symbol statement")

        self._assert_identifier(stmt.identifier, "PI", "symbol name")
        self._assert_node_type(stmt.expression, RealLiteral, "symbol value")

        self._assert_no_errors(parser)

    def test_variable_statement(self):
        """Тест оператора определения переменной"""
        parser = self._create_parser("var x: i32 = 10")
        self.assertIsNotNone(parser)

        stmt = parser.statement()
        self._assert_node_type(stmt, Variable, "variable statement")

        # Проверяем поле
        self._assert_node_type(stmt.field, Field, "variable field")
        self._assert_identifier(stmt.field.identifier, "x", "variable name")
        self._assert_name(stmt.field.type, ["i32"], "variable type")

        # Проверяем значение
        self._assert_node_type(stmt.expression, IntegerLiteral, "variable value")
        self.assertEqual(stmt.expression.value, 10)

        self._assert_no_errors(parser)

    def test_return_statement(self):
        """Тест оператора возврата"""
        test_cases = [
            ("return", None, "без значения"),
            ("return 42", 42, "со значением"),
            ("return x", "x", "с именем"),
        ]

        for source, expected_value, desc in test_cases:
            with self.subTest(f"Return: {desc}"):
                parser = self._create_parser(source)
                self.assertIsNotNone(parser)

                stmt = parser.statement()
                self._assert_node_type(stmt, Return, f"return statement {desc}")

                if expected_value is None:
                    self.assertIsNone(stmt.returns)
                elif isinstance(expected_value, int):
                    self._assert_node_type(stmt.returns, IntegerLiteral, "return value")
                    self.assertEqual(stmt.returns.value, expected_value)
                else:
                    self._assert_name(stmt.returns, [expected_value], "return name")

                self._assert_no_errors(parser)

    def test_assign_statement(self):
        """Тест оператора присваивания"""
        parser = self._create_parser("x = 10")
        self.assertIsNotNone(parser)

        stmt = parser.statement()
        self._assert_node_type(stmt, Assign, "assign statement")

        self._assert_name(stmt.name, ["x"], "assign target")
        self._assert_node_type(stmt.expression, IntegerLiteral, "assign value")

        self._assert_no_errors(parser)

    def test_function_call_statement(self):
        """Тест оператора вызова функции"""
        parser = self._create_parser('print("hello")')
        self.assertIsNotNone(parser)

        stmt = parser.statement()
        self._assert_node_type(stmt, FunctionCall, "function call statement")

        self._assert_name(stmt.name, ["print"], "function name")
        self.assertEqual(len(stmt.arguments), 1)
        self._assert_node_type(stmt.arguments[0], StringLiteral, "argument")

        self._assert_no_errors(parser)


class TestParserDeclarations(ParserTestBase):
    """Тесты парсинга объявлений"""

    def test_field_declaration(self):
        """Тест объявления поля"""
        parser = self._create_parser("x: i32")
        self.assertIsNotNone(parser)

        decl = parser.declaration()
        self._assert_node_type(decl, Field, "field declaration")

        self._assert_identifier(decl.identifier, "x", "field name")
        self._assert_name(decl.type, ["i32"], "field type")

        self._assert_no_errors(parser)

    def test_symbol_declaration(self):
        """Тест объявления символа"""
        parser = self._create_parser("def MAX_SIZE = 100")
        self.assertIsNotNone(parser)

        decl = parser.declaration()
        self._assert_node_type(decl, Symbol, "symbol declaration")

        self._assert_identifier(decl.identifier, "MAX_SIZE", "symbol name")
        self._assert_node_type(decl.expression, IntegerLiteral, "symbol value")

        self._assert_no_errors(parser)

    def test_variable_declaration(self):
        """Тест объявления переменной"""
        parser = self._create_parser("var counter: i32 = 0")
        self.assertIsNotNone(parser)

        decl = parser.declaration()
        self._assert_node_type(decl, Variable, "variable declaration")

        self._assert_identifier(decl.field.identifier, "counter", "variable name")
        self._assert_name(decl.field.type, ["i32"], "variable type")
        self._assert_node_type(decl.expression, IntegerLiteral, "initial value")

        self._assert_no_errors(parser)

    def test_public_declaration(self):
        """Тест публичного объявления"""
        parser = self._create_parser("pub var x: i32 = 10")
        self.assertIsNotNone(parser)

        decl = parser.declaration()
        self._assert_node_type(decl, Public, "public declaration")

        # Проверяем внутреннее объявление
        inner = decl.inner
        self._assert_node_type(inner, Variable, "inner variable declaration")
        self._assert_identifier(inner.field.identifier, "x", "public variable name")

        self._assert_no_errors(parser)


class TestParserComplexStructures(ParserTestBase):
    """Тесты парсинга сложных конструкций"""

    def test_nested_struct(self):
        """Тест вложенной структуры"""
        source = "struct { position: struct { x: i32, y: i32 }, name: string }"
        parser = self._create_parser(source)
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, StructType, "outer struct")

        self.assertEqual(len(expr.declarations), 2)

        # Первое поле - вложенная структура
        field1 = expr.declarations[0]
        self._assert_node_type(field1, Field, "nested struct field")
        self._assert_identifier(field1.identifier, "position", "field name")

        # Тип поля - структура
        self._assert_node_type(field1.type, StructType, "nested struct type")
        nested_struct = field1.type
        self.assertEqual(len(nested_struct.declarations), 2)

        self._assert_no_errors(parser)

    def test_function_with_complex_body(self):
        """Тест функции со сложным телом"""
        source = """
fn(x: i32) i32 {
    var result: i32 = x
    return result
}
"""
        parser = self._create_parser(source)
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, FunctionType, "function type")

        # Проверяем количество операторов
        self.assertEqual(len(expr.statements), 2)

        # Первый оператор - определение переменной
        stmt1 = expr.statements[0]
        self._assert_node_type(stmt1, Variable, "variable declaration")

        # Второй оператор - возврат
        stmt2 = expr.statements[1]
        self._assert_node_type(stmt2, Return, "return")

        self._assert_no_errors(parser)

    def test_pointer_to_array(self):
        """Тест указателя на массив"""
        parser = self._create_parser("*[10]i32")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, StarOperator, "pointer type")

        # Проверяем, что указатель указывает на массив
        self._assert_node_type(expr.type, ArrayType, "array type")

        self._assert_no_errors(parser)

    def test_array_of_pointers(self):
        """Тест массива указателей"""
        parser = self._create_parser("[5]*i32")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, ArrayType, "array type")

        # Проверяем, что элементы массива - указатели
        self._assert_node_type(expr.item_type, StarOperator, "pointer element type")

        self._assert_no_errors(parser)


class TestParserModule(ParserTestBase):
    """Тесты парсинга модуля"""

    def test_simple_module(self):
        """Тест простого модуля"""
        source = """
def PI = 3.14
var x: i32 = 10
pub var y: string = "hello"
"""
        parser = self._create_parser(source)
        self.assertIsNotNone(parser)

        module = parser.module()
        self._assert_node_type(module, StructType, "module")

        # Проверяем объявления
        self.assertEqual(len(module.declarations), 3)

        # Первое объявление - символ
        self._assert_node_type(module.declarations[0], Symbol, "first declaration")

        # Второе объявление - переменная
        self._assert_node_type(module.declarations[1], Variable, "second declaration")

        # Третье объявление - публичная переменная
        self._assert_node_type(module.declarations[2], Public, "third declaration")
        self._assert_node_type(module.declarations[2].inner, Variable, "public variable")

        self._assert_no_errors(parser)

    def test_module_with_functions(self):
        """Тест модуля с функциями"""
        source = """
def add = fn(x: i32, y: i32) i32 {
    return x
}

pub def multiply = fn(a: i32, b: i32) i32 {
    return a
}
"""
        parser = self._create_parser(source)
        self.assertIsNotNone(parser)

        module = parser.module()
        self._assert_node_type(module, StructType, "module")

        # Проверяем объявления
        self.assertEqual(len(module.declarations), 2)

        # Первое объявление - символ с функцией
        decl1 = module.declarations[0]
        self._assert_node_type(decl1, Symbol, "function symbol")
        self._assert_node_type(decl1.expression, FunctionType, "function value")

        # Второе объявление - публичный символ с функцией
        decl2 = module.declarations[1]
        self._assert_node_type(decl2, Public, "public function")
        self._assert_node_type(decl2.inner, Symbol, "inner symbol")

        self._assert_no_errors(parser)


class TestParserErrorHandling(ParserTestBase):
    """Тесты обработки ошибок"""

    def test_missing_semicolon_error(self):
        """Тест ошибки пропущенного двоеточия в поле"""
        parser = self._create_parser("x i32")  # Пропущено ':'
        self.assertIsNotNone(parser)

        decl = parser.declaration()
        self.assertIsNone(decl)
        self._assert_has_errors(parser)

    def test_missing_assign_error(self):
        """Тест ошибки пропущенного '=' в определении"""
        parser = self._create_parser("def PI 3.14")  # Пропущено '='
        self.assertIsNotNone(parser)

        decl = parser.declaration()
        self.assertIsNone(decl)
        self._assert_has_errors(parser)

    def test_missing_closing_brace(self):
        """Тест ошибки пропущенной закрывающей скобки"""
        parser = self._create_parser("struct { x: i32")  # Пропущено '}'
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self.assertIsNone(expr)
        self._assert_has_errors(parser)

    def test_invalid_array_size(self):
        """Тест ошибки недопустимого размера массива"""
        parser = self._create_parser("[x]i32")  # Размер должен быть целочисленным литералом
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self.assertIsNone(expr)
        self._assert_has_errors(parser)

    def test_unexpected_token(self):
        """Тест ошибки неожиданного токена"""
        parser = self._create_parser("=")  # Невалидное выражение
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self.assertIsNone(expr)  # Должен вернуть None
        self._assert_has_errors(parser)


class TestParserEdgeCases(ParserTestBase):
    """Тесты граничных случаев"""

    def test_empty_struct(self):
        """Тест пустой структуры"""
        parser = self._create_parser("struct {}")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, StructType, "empty struct")
        self.assertEqual(len(expr.declarations), 0)
        self._assert_no_errors(parser)

    def test_empty_function(self):
        """Тест пустой функции"""
        parser = self._create_parser("fn() void {}")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, FunctionType, "empty function")
        self.assertEqual(len(expr.statements), 0)
        self._assert_no_errors(parser)

    def test_function_with_empty_return(self):
        """Тест функции с пустым возвратом"""
        parser = self._create_parser("fn() void { return }")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, FunctionType, "function with empty return")

        self.assertEqual(len(expr.statements), 1)
        stmt = expr.statements[0]
        self._assert_node_type(stmt, Return, "return statement")
        self.assertIsNone(stmt.returns)

        self._assert_no_errors(parser)

    def test_complex_nested_expressions(self):
        """Тест сложных вложенных выражений"""
        parser = self._create_parser("*[]*struct { p: *[10]i32 }")
        self.assertIsNotNone(parser)

        expr = parser.expression()
        self._assert_node_type(expr, StarOperator, "outer pointer")

        # Проверяем вложенность
        self._assert_node_type(expr.type, SliceType, "slice")
        self._assert_node_type(expr.type.item_type, StarOperator, "pointer in slice")
        self._assert_node_type(expr.type.item_type.type, StructType, "struct in pointer")

        self._assert_no_errors(parser)


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
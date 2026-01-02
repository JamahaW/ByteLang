# node

узел АСД

---

# id(node)

Чистый идентификатор

Пример: `id_name_123`

---

# symbol(node)

Символ

`'def' <id> '=' <expr>`

---

# variable(node)

Переменная

`'var' <field> '=' <expr>`

---

# field(node)

Поле

`<id> ':' <type>`

---

# module(node)

Модуль

`[<declaration> '\n']*`

---

# call(node)

Вызов функции

`<name> '(' [<expr> [ ',' <expr> ]* ] ')'`

---

# function_signature

Сигнатура функции

`'fn' '(' <field> [',' <field>]* ')' <type>`

---

# expr(node)

Значение

---

# name(expr)

Разрешаемое имя

`<id> ['.' <name>]`

---

# literal_integer(expr)

Целочисленный литерал

`-12345`

---

# literal_real(expr)

Вещественный литерал

`-123.456`

---

# literal_string(expr)

Строковый литерал

`"string"`

---

# literal_list(expr)

Списковый литерал

`'{' <expr> [',' <expr>]* '}'`

---

# call_expr(expr)

Значение от вызова функции

`<call>`

---

# address_take(expr)

Операция взятия адреса

`'&' <name>`

---

# declaration(node)

Объявление

---

# pub(declaration)

Сделать объявление публичным

`'pub' <declaration>`

---

# symbol_declaration(declaration)

Задать символ

`<symbol>`

---

# variable_declaration(declaration)

Задать переменную

`<variable>`

---

# field_declaration(declaration)

Задать поле

`<field>`

---

# statement(node)

Statement (Строка внутри функции)

---

# local_symbol(statement)

Задать локальный символ внутри функции

`<symbol>`

---

# local_variable(statement)

Задать локальную переменную внутри функции

`<variable>`

---

# assign(statement)

Выполнить присвоение значения идентификатору

`<name> '=' <expr>`

---

# call_statement(statement)

Вызвать функцию

`<call>`

---

# return(statement)

Возврат значения

`'return' [<expr>]`


---

# type(expr)

Узел типа

---

# pointer_type(type)

Указатель на тип

`'*' <type>`

---

# array_type(type)

Массив

`'[' <expr> ']' <type>`

---

# slice_type(type)

Срез

`'[' ']' <type>`

---

# function_signature_type(type)

Тип сигнатуры функции

`<function_signature>`

---

# pure_type(type)

---

Чистый тип

`<name>`

---

# struct_type(type)

---

Структура

`'struct' '{' <module> '}'`

# function_type(type)

---

Функция

`<function_signature> '{' [<statement> '\n']* '}' `

---
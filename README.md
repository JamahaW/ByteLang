# **BYTELANG**

Интерпретируемый низкоуровневый язык программирования.

## Структура программы

Скомпилированный байткод - программа

Программа состоит из следующих основных частей:

- data - данные о программе (Версия байткода, индекс начала code)
- heap - Область хранения всех переменных
- code - Область, где подряд записываются выполняемые инструкции с их аргументами

## Типы файлов ByteLang

- `bls` — (ByteLang Source) - исходный байткод (обычный текстовый файл)
- `blc` — (ByteLang Compiled) - скомпилированный байткод (простой двоичный файл)
- `blp` — (ByteLang Package) - пакет инструкций (обычный текстовый файл)

## Примитивные типы данных:

Таблица соответствия ByteLang - тип C++

- `i8 - int8_t`
- `u8 - uint8_t`
- `i16 - int16_t`
- `u16 - uint16_t`
- `i32 - int32_t`
- `u32 - uint32_t`
- `i64 - int64_t`
- `u64 - uint64_t`
- `f32 - float` (Пока не реализован)
- `f64 - double` (Пока не реализован)

## Виды конфигурационных файлов

- Пакет инструкций (package) (blp) Имеет вид:

  Компилятор будет искать в папке packages
    - Каждая строка содержит запись: `<name> <T..>`
    - Для комментариев используется #
    - name - идентификатор
    - T - тип ByteLang ('*' после T значит, что инструкция принимает указатель и приведёт значение к этому типу)

  Например:

  ```blp
  print i32* # вывод человекочитаемого значения
  exit u8 # завершение программы
  goto u16
  ```

- Профиль виртуальной машины (profile) (json) Имеет вид:

  Компилятор будет искать в папке profiles

    - prog_len - максимальный размер программы (null или не указывать поле чтобы без ограничений)
    - ptr_prog - размер в байтах указателя инструкции, ограничивает prog_len
    - ptr_heap - размер в байтах указателя на кучу, ограничивает размер кучи
    - ptr_inst - размер в байтах индекса инструкции (имеется ввиду, что индекс - это указатель в массиве инструкций)
    - ptr_type - размер в байтах под данные типа переменной (Переменная в памяти храниться в виде структуры
      `{ptr_type, ptr_value}` ptr_value имеет тип и размер соответствующий ptr_type)

  Например:
  ```json
  {
    "prog_len": 512,
    "ptr_prog": 2,
    "ptr_heap": 1,
    "ptr_inst": 1,
    "ptr_type": 1
  }
  ```

- Параметры окружения (environment) (json) Имеет вид:

  Компилятор будет искать в папке environments
    - profile - идентификатор Параметров виртуальной машины
    - packages - список пакетов команд, которые реализованы в данной ВМ

  Например:
  ```json
  {
    "profile": "avr",
    "packages": [
      "base",
      "io",
      "stack",
      "math"
    ]
  }
  ```

## Грамматика

Синтаксическое дерево упрощено - это линейная последовательность Statement

- `Statement = Directive_use | Instruction_call | Mark`
- `Directive_use = .<name> <args..>`
- `Instruction_call = <name> <args..>`
- `Mark = <name>:`

*Комментарий обозначается `'#'`

Вот фрагмент кода, удовлетворяющий данной грамматике

```bls
.env env_test

my_mark:

instr_test 123
```

Метки

Метки используются для обозначения определенных точек в коде.\
Формат метки: `<name>:`\
Пример:
`mark:`

Директивы

Директивы используются для операций над кодом во время компиляции

- `env <env_name>` - Использовать окружение env_name
    - Вызывается один раз, обычно самой первой строчкой

- `ptr <T> <name> <value>` объявить указатель.\
  Пример: `.ptr i32 abc 12345`
    - объявить указатель abc типа i32 с значением 12345`
    - T должен соответствовать одному из существующих типов
    - повторное объявление с существующим идентификатором недопустимо
    - значение value должно быть допустимым для типа данных указателя

- `def <name> <value>` Объявить макро константу.\
  Пример: `.def TIMER_MAX_MS 1200`
    - повторное объявление с существующим идентификатором недопустимо
    - Можно указывать выражение
    - В выражении в качестве операндов могут быть только константы и метки

Инструкции

запись : `<name> <arg1> <arg2> ...`

# Процесс компиляции и исполнения

Для примера рассмотрим следующую ситуацию:

Определено окружение `environments/example_env.json`

```json
{
  "profile": "example_profile",
  "packages": [
    "example_package"
  ]
}
```

Файл `primitive_types.json` определяет какие примитивные типы данных существуют.
Достаточно очевидная структура.

```json
{
  "u8": {
    "signed": false,
    "size": 1
  },
  "i16": {
    "signed": true,
    "size": 2
  },
  "u32": {
    "signed": false,
    "size": 4
  }
}
```

Файл профиля виртуальной машины `profiles/example_profile.json`

```json
{
  "ptr_prog": 2,
  "ptr_heap": 1,
  "ptr_inst": 1,
  "ptr_type": 1
}
```

Файл пакета инструкций `packages/example_package.bls`

```bls
exit u8
test i16* u8 u32
```

Используя все перечисленные выше настройки компилятора, получится написать следующи код:

```bls
.env example_env

# объявлем константы A = 10, B = 25
.def A 10
.def B 25

# выделяем область в heap под переменную примитивного типа i16 
# со значением -12345 и получаем её адрес под псевдонимом x (сам по себе x - просто константное число (адрес) )
.ptr i16 x -12345

# аналогично
.ptr u8 y 123 

# вызываем инструкцию test, передаём 
# адрес переменной x
# значение A
# значение B
test x A   B

# аналогично
test y  B   x

exit    88
```

## Лексический анализ

Если упростить процесс и опустить детали, то получается следующий алгоритм:

Файл исходного кода считывается построчно, пустые и закомментированные сроки пропускаются.
Если бы мы увидели как такой код выглядит, то получили бы такой результат:

```bls
.env example_env
.def A 10
.def B 25
.ptr i16 x -12345
.ptr u8 y 123 
test x A B
test y B x
exit 88
```

Каждая строка - Statement, который может быть 3 типов: DIRECTIVE_USE | INSTRUCTION_CALL | MARK

Соответственно определяем тип выражения и пакуем данные, предварительно проверив, что лексемы соответствуют регулярным выражениям

```
  0: DIRECTIVE_USE@0                  env(example_env)   
  1: DIRECTIVE_USE@1                  def(A, 10)         
  2: DIRECTIVE_USE@2                  def(B, 25)         
  3: DIRECTIVE_USE@3                  ptr(i16, x, -12345)
  4: DIRECTIVE_USE@4                  ptr(u8, y, 123)    
  5: INSTRUCTION_CALL@5               test(x, A, B)      
  6: INSTRUCTION_CALL@6               test(y, B, x)      
  7: INSTRUCTION_CALL@7               exit(88)           
```

Начинаем обработку выражений и генерируем промежуточный код. Разберу несколько из них.





# TODO

для функций придумать штуку, которая отправляет в стек кусок HEAP от 0 до размера всех переменных внутри функции
И в runtime размечать там переменные

TODO Продвинутый синтаксис, расчёт константных выражений

TODO стековая передача и возврат инструкций
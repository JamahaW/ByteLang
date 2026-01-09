# ByteLang

Экспериментальный язык программирования. Типы — выражения первого класса. Метапрограммирование в ядре.

## Текущий статус

**Работает:**

- Лексер (токены, числа, строки, ключевые слова)
- Парсер (Pratt-парсинг, AST)
- Полная грамматика языка

## Грамматика

### Базовые конструкции

```rust
def name = expression           // символ
pub def name = expression      // публичный символ
var name: type = value         // переменная
```

### Типы

```rust
*u8                           // указатель
[256]u8                       // массив
[]u8                          // срез
sig (u8, i32) void            // сигнатура функции
fn (a: u8, b: i32) void { }   // тип функции (с телом)
struct { x: i32, y: i32 }     // структура
```

### Операторы

```rust
x + y, x - y, x * y, x / y, x % y
x == y, x != y, x < y, x > y, x <= y, x >= y
x & y, x | y, x ^ y, x << y, x >> y
x and y, x or y, not x
+x, -x, &x, *x
```

### Управление

```rust
if condition { } else { }
loop { break; continue; }
return value
```

### Пример

```rust
def math = import("math.bl")

pub def Vector3 = struct {
    x: f32
    y: f32
    z: f32
}

def add = fn(a: i32, b: i32) i32 {
    return a + b
}

pub def main = fn() void {
    var x: i32 = 10
    var y: i32 = 20
    var sum = add(x, y)
    
    if sum > 0 {
        math.print("Positive")
    }
}
```

## Архитектура

### Реализовано:

- `lexer.py` — токенизация
- `token.py` — типы токенов
- `ast.py` — AST-узлы
- `parser.py` — синтаксический анализ

### В разработке:

- Семантический анализ
- Проверка типов
- Генерация кода

## Философия

1. Типы = выражения
2. Минимальный синтаксис
3. Контроль над памятью
4. Метапрограммирование в ядре

## Лицензия

MIT

#include <cstdio>
#include "ByteLang.hpp"
#include "commands.hpp"

namespace cmd {
BL::VmVariables* vars = nullptr;
BL::Vector<int16_t>* value_stack = nullptr;
BL::Vector<int16_t>* call_stack = nullptr;

BL::Instruction instruction_table[] = {
    { c_exit, WORD, "EXIT" },                             // 0
    { c_wait, BYTE_1, "WAIT" },                           // 1
    { c_move, BYTE_2, "MOVE" },                           // 2
    { c_print, BYTE_1, "PRINT" },                         // 3
    { c_not, BYTE_2, "NOT" },                             // 4
    { c_not2, BYTE_1, "NOT2" },                           // 5
    { c_and, BYTE_3, "AND" },                             // 6
    { c_or, BYTE_3, "OR" },                               // 7
    { c_inc, BYTE_1, "INC" },                             // 8
    { c_dec, BYTE_1, "DEC" },                             // 9
    { c_add, BYTE_3, "ADD" },                             // 10
    { c_add2, BYTE_2, "ADD2" },                           // 11
    { c_sub, BYTE_3, "SUB" },                             // 12
    { c_sub2, BYTE_2, "SUB2" },                           // 13
    { c_mul, BYTE_3, "MUL" },                             // 14
    { c_mul2, BYTE_2, "MUL2" },                           // 15
    { c_div, BYTE_3, "DIV" },                             // 16
    { c_div3, BYTE_3, "DIV3" },                           // 17
    { c_div2, BYTE_2, "DIV2" },                           // 18
    { c_call, WORD, "CALL" },                             // 19
    { c_return, VOID, "RETURN" },                         // 20
    { c_push, BYTE_1, "PUSH" },                           // 21
    { c_pop, BYTE_1, "POP" },                             // 22
    { c_goto, WORD, "GOTO" },                             // 23
    { c_goto_equals, WORD, "GOTO_EQUALS" },               // 24
    { c_goto_not_equals, WORD, "GOTO_NOT_EQUALS" },       // 25
    { c_goto_greater, WORD, "GOTO_GREATER" },             // 26
    { c_goto_less, WORD, "GOTO_LESS" },                   // 27
    { c_compare, BYTE_2, "COMPARE" },                     // 28
    { c_compare_zero, BYTE_1, "COMPARE_ZERO" },           // 29
    { c_compare_one, BYTE_1, "COMPARE_ONE" },             // 30
    { c_put_equals, BYTE_1, "PUT_EQUALS" },               // 31
    { c_put_not_equals, BYTE_1, "PUT_NOT_EQUALS" },       // 32
    { c_put_greater, BYTE_1, "PUT_GREATER" },             // 33
    { c_put_less, BYTE_1, "PUT_LESS" },                   // 34
    { c_speed_servo, BYTE_1, "SPEED_SERVO" },             // 35
    { c_speed_motor, BYTE_1, "SPEED_MOTOR" },             // 36
    { c_servo, BYTE_2, "SERVO" },                         // 37
    { c_turn_left, BYTE_1, "TURN_LEFT" },                 // 38
    { c_turn_right, BYTE_1, "TURN_RIGHT" },               // 39
    { c_turn_center, BYTE_1, "TURN_CENTER" },             // 40
    { c_turn_cross_left, VOID, "TURN_CROSS_LEFT" },       // 41
    { c_turn_cross_right, VOID, "TURN_CROSS_RIGHT" },     // 42
    { c_ride_dist, BYTE_1, "RIDE_DIST" },                 // 43
    { c_ride_wall, BYTE_1, "RIDE_WALL" },                 // 44
    { c_ride_cross, BYTE_1, "RIDE_CROSS" },               // 45
    { c_ride_time, BYTE_1, "RIDE_TIME" },                 // 46
    { c_line_dist, BYTE_1, "LINE_DIST" },                 // 47
    { c_line_wall, BYTE_1, "LINE_WALL" },                 // 48
    { c_line_cross, BYTE_1, "LINE_CROSS" },               // 49
    { c_line_timer, BYTE_1, "LINE_TIMER" },               // 50
};

}
void cmd::setContext(BL::Interpreter& interpreter) {
    cmd::vars = &interpreter.getVariables(); // получаем переменные интерпретатора
    // передаём таблицу команд
    interpreter.getInstructions().init(instruction_table, sizeof(instruction_table) / sizeof(BL::Instruction));
    cmd::value_stack = &interpreter.getStack();
    cmd::call_stack = &interpreter.getCall();
}

static inline int16_t& arg(uint8_t index) {
    return cmd::vars->get(index);
}

static inline int16_t word() {
    return cmd::vars->word_arg;
}

static void setIP(int16_t ip) {
    cmd::vars->ip = ip;
}

static void setIPword() {
    setIP(word());
}

void c_exit() {
    cmd::vars->running = false;
    cmd::vars->exit_status = cmd::vars->word_arg;
}
void c_wait() { }
void c_goto() {
    setIPword();
}
void c_goto_equals() {
    if(cmd::vars->flag_equals) setIPword();
}
void c_goto_not_equals() {
    if(cmd::vars->flag_notEquals) setIPword();
}
void c_goto_greater() {
    if(cmd::vars->flag_greater) setIPword();
}
void c_goto_less() {
    if(cmd::vars->flag_less) setIPword();
}
void c_call() {
    setIP(word());
    cmd::call_stack->push(word());
}
void c_return() {
    setIP(cmd::call_stack->pop());
}
void c_push() {
    cmd::value_stack->push(arg(0));
}
void c_pop() {
    arg(0) = cmd::value_stack->pop();
}
void c_move() {
    // A, B:    B = A
    arg(0) = arg(1);
}

static void compare_value(int16_t value) {
    int16_t num = arg(0);
    cmd::vars->flag_equals = num == value;
    cmd::vars->flag_notEquals = num != value;
    cmd::vars->flag_greater = num > value;
    cmd::vars->flag_less = num < value;
}

void c_compare() {
    // A, B
    compare_value(arg(1));
}
void c_compare_zero() {
    compare_value(0);
}
void c_compare_one() {
    compare_value(1);
}
void c_put_equals() {
    arg(0) = cmd::vars->flag_equals;
}
void c_put_not_equals() {
    arg(0) = cmd::vars->flag_notEquals;
}
void c_put_greater() {
    arg(0) = cmd::vars->flag_greater;
}
void c_put_less() {
    arg(0) = cmd::vars->flag_less;
}
void c_not() {
    // A = !B
    arg(0) = !(arg(1));
}
void c_not2() {
    // A = !A
    arg(0) = !arg(0);
}
void c_and() {
    // C = A && B
    arg(0) = arg(1) && arg(2);
}
void c_or() {
    // C = A || B
    arg(0) = arg(1) || arg(2);
}
void c_inc() {
    arg(0)++;
}
void c_dec() {
    arg(0)--;
}
void c_add() {
    // C = A + B
    arg(0) = arg(1) + arg(2);
}
void c_add2() {
    // A += B
    arg(0) += arg(1);
}
void c_sub() {
    // C = A - B
    arg(0) = arg(1) - arg(2);
}
void c_sub2() {
    // A -= B
    arg(0) -= arg(1);
}
void c_mul() {
    // C = A * B
    arg(0) = arg(1) * arg(2);
}
void c_mul2() {
    // A *= B
    arg(0) *= arg(1);
}
void c_div() {
    // C = A / B
    arg(0) = arg(1) / arg(2);
}
void c_div3() {
    /*
    div C A B     C = A / B     деление
    div3 C var_a VarA     C = VarA / var_b     составное деление
    div2 C A     C = C / A     деление альтернативное
    */
}
void c_div2() {
    // A /= B
    arg(0) /= arg(1);
}

void c_print() {
    std::printf("|-> %d\n", arg(0));
}
void c_speed_servo() { }
void c_speed_motor() { }
void c_servo() { }
void c_turn_left() { }
void c_turn_right() { }
void c_turn_center() { }
void c_turn_cross_left() { }
void c_turn_cross_right() { }
void c_ride_dist() { }
void c_ride_wall() { }
void c_ride_cross() { }
void c_ride_time() { }
void c_line_dist() { }
void c_line_wall() { }
void c_line_cross() { }
void c_line_timer() { }

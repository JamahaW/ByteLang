#ifndef COMMANDS_H_INCLUDED
#define COMMANDS_H_INCLUDED

#include "ByteLang.hpp"

namespace cmd {
    extern BL::VmVariables* vars;
    void setContext(BL::Interpreter & interpreter); // настроить текущий интерптетатор под данный набор команд
}

void c_exit();
void c_wait();
void c_goto();
void c_goto_equals();
void c_goto_not_equals();
void c_goto_greater();
void c_goto_less();
void c_call();
void c_return();
void c_push();
void c_pop();
void c_move();
void c_compare();
void c_compare_zero();
void c_compare_one();
void c_put_equals();
void c_put_not_equals();
void c_put_greater();
void c_put_less();
void c_not();
void c_not2();
void c_and();
void c_or();
void c_inc();
void c_dec();
void c_add();
void c_add2();
void c_sub();
void c_sub2();
void c_mul();
void c_mul2();
void c_div();
void c_div3();
void c_div2();
void c_print();
void c_speed_servo();
void c_speed_motor();
void c_servo();
void c_turn_left();
void c_turn_right();
void c_turn_center();
void c_turn_cross_left();
void c_turn_cross_right();
void c_ride_dist();
void c_ride_wall();
void c_ride_cross();
void c_ride_time();
void c_line_dist();
void c_line_wall();
void c_line_cross();
void c_line_timer();

#endif // COMMANDS_H_INCLUDED

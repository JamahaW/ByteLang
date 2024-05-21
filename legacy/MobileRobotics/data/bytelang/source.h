
///////////////   BYTELANG COMMANDS HEADERS   ///////////////

void c_exit();  
void c_wait();  
void c_move();  
void c_print();  
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
void c_call();  
void c_return();  
void c_push();  
void c_pop();  
void c_goto();  
void c_goto_equals();  
void c_goto_not_equals();  
void c_goto_greater();  
void c_goto_less();  
void c_compare();  
void c_compare_zero();  
void c_compare_one();  
void c_put_equals();  
void c_put_not_equals();  
void c_put_greater();  
void c_put_less();  
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

static vm_command_t vm_commands[] {
  { c_exit            , WORD  , "EXIT" }             ,  // 0
  { c_wait            , BYTE_1, "WAIT" }             ,  // 1
  { c_move            , BYTE_2, "MOVE" }             ,  // 2
  { c_print           , BYTE_1, "PRINT" }            ,  // 3
  { c_not             , BYTE_2, "NOT" }              ,  // 4
  { c_not2            , BYTE_1, "NOT2" }             ,  // 5
  { c_and             , BYTE_3, "AND" }              ,  // 6
  { c_or              , BYTE_3, "OR" }               ,  // 7
  { c_inc             , BYTE_1, "INC" }              ,  // 8
  { c_dec             , BYTE_1, "DEC" }              ,  // 9
  { c_add             , BYTE_3, "ADD" }              ,  // 10
  { c_add2            , BYTE_2, "ADD2" }             ,  // 11
  { c_sub             , BYTE_3, "SUB" }              ,  // 12
  { c_sub2            , BYTE_2, "SUB2" }             ,  // 13
  { c_mul             , BYTE_3, "MUL" }              ,  // 14
  { c_mul2            , BYTE_2, "MUL2" }             ,  // 15
  { c_div             , BYTE_3, "DIV" }              ,  // 16
  { c_div3            , BYTE_3, "DIV3" }             ,  // 17
  { c_div2            , BYTE_2, "DIV2" }             ,  // 18
  { c_call            , WORD  , "CALL" }             ,  // 19
  { c_return          , VOID  , "RETURN" }           ,  // 20
  { c_push            , BYTE_1, "PUSH" }             ,  // 21
  { c_pop             , BYTE_1, "POP" }              ,  // 22
  { c_goto            , WORD  , "GOTO" }             ,  // 23
  { c_goto_equals     , WORD  , "GOTO_EQUALS" }      ,  // 24
  { c_goto_not_equals , WORD  , "GOTO_NOT_EQUALS" }  ,  // 25
  { c_goto_greater    , WORD  , "GOTO_GREATER" }     ,  // 26
  { c_goto_less       , WORD  , "GOTO_LESS" }        ,  // 27
  { c_compare         , BYTE_2, "COMPARE" }          ,  // 28
  { c_compare_zero    , BYTE_1, "COMPARE_ZERO" }     ,  // 29
  { c_compare_one     , BYTE_1, "COMPARE_ONE" }      ,  // 30
  { c_put_equals      , BYTE_1, "PUT_EQUALS" }       ,  // 31
  { c_put_not_equals  , BYTE_1, "PUT_NOT_EQUALS" }   ,  // 32
  { c_put_greater     , BYTE_1, "PUT_GREATER" }      ,  // 33
  { c_put_less        , BYTE_1, "PUT_LESS" }         ,  // 34
  { c_speed_servo     , BYTE_1, "SPEED_SERVO" }      ,  // 35
  { c_speed_motor     , BYTE_1, "SPEED_MOTOR" }      ,  // 36
  { c_servo           , BYTE_2, "SERVO" }            ,  // 37
  { c_turn_left       , BYTE_1, "TURN_LEFT" }        ,  // 38
  { c_turn_right      , BYTE_1, "TURN_RIGHT" }       ,  // 39
  { c_turn_center     , BYTE_1, "TURN_CENTER" }      ,  // 40
  { c_turn_cross_left , VOID  , "TURN_CROSS_LEFT" }  ,  // 41
  { c_turn_cross_right, VOID  , "TURN_CROSS_RIGHT" } ,  // 42
  { c_ride_dist       , BYTE_1, "RIDE_DIST" }        ,  // 43
  { c_ride_wall       , BYTE_1, "RIDE_WALL" }        ,  // 44
  { c_ride_cross      , BYTE_1, "RIDE_CROSS" }       ,  // 45
  { c_ride_time       , BYTE_1, "RIDE_TIME" }        ,  // 46
  { c_line_dist       , BYTE_1, "LINE_DIST" }        ,  // 47
  { c_line_wall       , BYTE_1, "LINE_WALL" }        ,  // 48
  { c_line_cross      , BYTE_1, "LINE_CROSS" }       ,  // 49
  { c_line_timer      , BYTE_1, "LINE_TIMER" }       ,  // 50
};

#define vm_commands_SIZE ( sizeof(vm_commands) )
#define vm_commands_LENGTH ( sizeof(vm_commands) / sizeof(vm_command_t) )


/////////////////////////   SOURCE   /////////////////////////

void c_exit() { /* word */ }
void c_wait() { /* byte_1 */ }
void c_move() { /* byte_2 */ }
void c_print() { /* byte_1 */ }
void c_not() { /* byte_2 */ }
void c_not2() { /* byte_1 */ }
void c_and() { /* byte_3 */ }
void c_or() { /* byte_3 */ }
void c_inc() { /* byte_1 */ }
void c_dec() { /* byte_1 */ }
void c_add() { /* byte_3 */ }
void c_add2() { /* byte_2 */ }
void c_sub() { /* byte_3 */ }
void c_sub2() { /* byte_2 */ }
void c_mul() { /* byte_3 */ }
void c_mul2() { /* byte_2 */ }
void c_div() { /* byte_3 */ }
void c_div3() { /* byte_3 */ }
void c_div2() { /* byte_2 */ }
void c_call() { /* word */ }
void c_return() { /* void */ }
void c_push() { /* byte_1 */ }
void c_pop() { /* byte_1 */ }
void c_goto() { /* word */ }
void c_goto_equals() { /* word */ }
void c_goto_not_equals() { /* word */ }
void c_goto_greater() { /* word */ }
void c_goto_less() { /* word */ }
void c_compare() { /* byte_2 */ }
void c_compare_zero() { /* byte_1 */ }
void c_compare_one() { /* byte_1 */ }
void c_put_equals() { /* byte_1 */ }
void c_put_not_equals() { /* byte_1 */ }
void c_put_greater() { /* byte_1 */ }
void c_put_less() { /* byte_1 */ }
void c_speed_servo() { /* byte_1 */ }
void c_speed_motor() { /* byte_1 */ }
void c_servo() { /* byte_2 */ }
void c_turn_left() { /* byte_1 */ }
void c_turn_right() { /* byte_1 */ }
void c_turn_center() { /* byte_1 */ }
void c_turn_cross_left() { /* void */ }
void c_turn_cross_right() { /* void */ }
void c_ride_dist() { /* byte_1 */ }
void c_ride_wall() { /* byte_1 */ }
void c_ride_cross() { /* byte_1 */ }
void c_ride_time() { /* byte_1 */ }
void c_line_dist() { /* byte_1 */ }
void c_line_wall() { /* byte_1 */ }
void c_line_cross() { /* byte_1 */ }
void c_line_timer() { /* byte_1 */ }

#pragma once

#include <cstdint>
#include <cstring>

enum Signatures {
    //          ID | SIZE
    VOID   = (0x00 | 0),
    WORD   = (0x10 | 2),
    BYTE_1 = (0x20 | 1),
    BYTE_2 = (0x30 | 2),
    BYTE_3 = (0x40 | 3),
    ARG_COUNT_MAX = 3,
};

namespace BL {

typedef void (*CallBack)(void);

struct Instruction {
    CallBack execute;
    Signatures signature;
    const char* name;

    inline uint8_t getSize() {
        return (uint8_t) signature & 0x0f;
    }
};

typedef void (*InstructionHandler)(Instruction&);

template <typename T> struct Vector {
    T* data = nullptr;
    uint16_t size = 0;
    uint16_t end = 0;

    void init(T* source, uint16_t _size) {
        data = source;
        size = _size;
    }

    void push(T value) {
        data[end++] = value;
    }

    T pop() {
        return data[--end];
    }

    void load(T* values, uint16_t len) {
        std::memcpy(data, values, (end = len));
    }
};

struct VmVariables {
    uint16_t ip = 0;
    bool running = false;

    bool flag_equals = false;
    bool flag_notEquals = false;
    bool flag_greater = false;
    bool flag_less = false;

    int16_t word_arg = 0;
    int16_t exit_status = 0;

    uint16_t pointer_args[ARG_COUNT_MAX] {0};

    uint8_t* program_offset;

    VmVariables() {}

    int16_t& get(uint8_t arg_index) {
        return *(int16_t*)(program_offset + pointer_args[arg_index]);
    }
};

class Interpreter {

  private:
    Vector<uint8_t> program;
    Vector<int16_t> stack;
    Vector<int16_t> call;
    Vector<Instruction> instructions;
    InstructionHandler instructionHandler = nullptr;
    VmVariables variables;

    template <typename T> T getArg(uint8_t offset);

  public:
    Interpreter() {}

    Vector<Instruction>& getInstructions();
    Vector<uint8_t>& getProgram();
    Vector<int16_t>& getStack();
    Vector<int16_t>& getCall();
    VmVariables& getVariables();

    int16_t run();
    void setInstructionHandler(InstructionHandler IH);
};

}

#include "ByteLang.hpp"

using namespace BL;

int16_t Interpreter::run() {
    variables.program_offset = program.data;
    variables.ip = program.data[0];
    variables.running = true;

    while(variables.running && (variables.ip < program.end)) {
        uint8_t index = program.data[variables.ip];
        bool inline_flag = (index & 0b10000000) != 0;
        index &= 0b01111111;

        if(index > instructions.size)
            goto ERROR_INVALID_COMMAND;

        Instruction& instruction = instructions.data[index];
        uint8_t offset = instruction.getSize();

        if(offset > 0) { // !VOID
            if(instruction.signature != WORD) {
                for(uint8_t i = 0, end = offset - inline_flag; i <= end; i++) {
                    uint16_t value = (uint16_t)getArg<uint8_t>(i);
                    variables.pointer_args[i] = value;
                }

                if(inline_flag)
                    variables.pointer_args[offset - 1] = variables.ip + offset;

            } else
                variables.word_arg = getArg<int16_t>(0);
        }

        variables.ip += 1 + offset + inline_flag;
        instruction.execute();

        if(instructionHandler != nullptr) instructionHandler(instruction);
    }

    return variables.exit_status;
ERROR_INVALID_COMMAND:
    return -1; // была попытка вызвать команду с индексом за таблицей команд
}

void Interpreter::setInstructionHandler(InstructionHandler IH) {
    instructionHandler = IH;
}

template <typename T> T Interpreter::getArg(uint8_t offset) {
    return *(T*)(program.data + variables.ip + offset + 1);
}

VmVariables& Interpreter::getVariables() {
    return variables;
}

Vector<int16_t>& Interpreter::getStack() {
    return stack;
}

Vector<int16_t>& Interpreter::getCall() { return call; }

Vector<uint8_t>& Interpreter::getProgram() {
    return program;
}

Vector<Instruction>& Interpreter::getInstructions() {
    return instructions;
}

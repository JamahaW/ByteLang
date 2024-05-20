#include <cstdint>
#include <cstdio>

// #include <conio.h>

#include "ByteLang.hpp"
#include "commands.hpp"

template <typename T> void printVector(const BL::Vector<T>& vector) {
    for (uint16_t i = 0; i < vector.end; i++) {
        std::printf("%d ", vector.data[i]);
    }
    std::puts("\n");
}

// Функция-образ
void executeHandler(BL::Instruction& instruction) {
    uint16_t* args = cmd::vars->pointer_args;

    std::printf("%3u: %s \t W:%5d [%5u, %5u, %5u]\n",
                cmd::vars->ip, instruction.name,
                cmd::vars->word_arg, args[0], args[1], args[2]);
}

/* Инициализация интерпретатора */
void setup(BL::Interpreter& vm) {
    cmd::setContext(vm); // инициализация контекста
    vm.setInstructionHandler(executeHandler);
    static uint8_t program_memory[512]; // буфер под выполнение программы
    static int16_t value_stack[32]; // буфер под стек значений
    static int16_t call_stack[32];  // буфер для стека вызовов

    vm.getProgram().init(program_memory, sizeof(program_memory));
    vm.getStack().init(value_stack, sizeof(value_stack));
    vm.getCall().init(call_stack, sizeof(call_stack));
}

/* Загрузка программы */
void loadArray(BL::Interpreter& vm, uint8_t* program, uint16_t len) {
    vm.getProgram().load(program, len);
}

/* Загрузка программы из файла -> удалось считать*/
bool loadFile(BL::Interpreter& vm, const char* filename) {
    uint16_t size, readed;
    const char* error = nullptr;
    FILE* file = std::fopen(filename, "rb");
    BL::Vector<uint8_t>& buffer = vm.getProgram();

    if(!file) {
        error = "Failed to open file";
        goto reader_exit;
    }

    // Определение размера файла
    std::fseek(file, 0, SEEK_END);
    size = std::ftell(file);
    std::rewind(file);

    // Проверка размера буфера
    if(size > buffer.size) {
        error = "Buffer size is too small";
        goto reader_close;
    }

    buffer.end = size;
    readed = std::fread(buffer.data, 1, size, file); // Чтение данных из файла

    // Проверка на ошибки чтения
    if(readed != size) {
        error = "ReadError";
        goto reader_close;
    }

reader_close:
    std::fclose(file);
reader_exit:

    if(error != nullptr) {
        std::printf("FileReader Error: %s!\n", error);
        return false;
    }

    return true;
}

int main(int argc, char* argv[]) {
    int16_t ret;
    const char* select;
    BL::Interpreter vm;

    setup(vm);

    select = "eternal";
    select = (argc == 2) ? argv[1] : "A:/Projects/ScriptingLanguage/ByteLangVirtualMashine/bin/debug/example.dat";

    if(!loadFile(vm, select)) return 2;
    printVector(vm.getProgram());

    std::printf("running '%s' program\n", select);
    ret = vm.run();
    std::printf("program exit with code: %d\n", ret);

    return 0;
}

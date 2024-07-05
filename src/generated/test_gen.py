"""env: 'test_gen' from 'A:\\Projects\\ByteLang\\data\\environments\\test_gen.json'"""
from bytelang.interpreters import Interpreter


def __avr_test_exit__u8(vm: Interpreter) -> None:
    """[2B] test::exit@0(std::u8)"""
    const_u8_0 = vm.ipReadPrimitive(vm.u8)
    vm.setExitCode(const_u8_0)


def __avr_test_print__u32_ptr(vm: Interpreter) -> None:
    """[2B] test::print@1(std::u8*(std::u32))"""
    var_u32_0 = vm.ipReadHeapPointer()
    vm.stdoutWrite(f"|> {vm.addressReadPrimitive(var_u32_0, vm.u32)}\n")


INSTRUCTIONS = (__avr_test_exit__u8, __avr_test_print__u32_ptr)

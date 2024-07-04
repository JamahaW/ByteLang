from typing import Iterable
from typing import Optional

from bytelang.codegenerator import CodeInstruction
from bytelang.codegenerator import ProgramData
from bytelang.handlers import BasicErrorHandler


class ByteCodeGenerator:

    def __init__(self, error_handler: BasicErrorHandler) -> None:
        self.__err = error_handler.getChild(self.__class__.__name__)

    def run(self, instructions: Iterable[CodeInstruction], data: Optional[ProgramData]) -> Optional[bytes]:
        if data is None:
            self.__err.write("Program data is None")
            return

        ret = bytearray()
        profile = data.environment.profile

        ret.extend(profile.pointer_heap.write(data.start_address))

        for v in data.variables:
            ret.extend(v.write(profile.type_index))

        for ins in instructions:
            ret.extend(ins.write(profile.instruction_index))

        if profile.max_program_length is not None and profile.max_program_length < len(ret):
            self.__err.write(f"program size ({len(ret)}) out of {profile.max_program_length}")
            return

        return bytes(ret)

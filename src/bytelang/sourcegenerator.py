"""Генераторы кода для виртуальных машин"""
from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from enum import auto
from pathlib import Path
from typing import Iterable
from typing import Optional

from bytelang.content import Environment
from bytelang.content import EnvironmentInstruction
from bytelang.content import EnvironmentInstructionArgument
from bytelang.interpreters import Interpreter
from bytelang.registries import PrimitivesRegistry
from bytelang.tools import ReprTool


class Language(Enum):
    PYTHON = auto()
    C_PLUS_PLUS = auto()
    C = auto()


@dataclass(kw_only=True, frozen=True)
class GenerationSettings:
    vm_instance: str
    vm_class: str
    vm_method_ipReadPrimitive: str
    vm_method_ipReadHeapPointer: str


class InstructionSourceGenerator(ABC):

    @staticmethod
    def create(lang: Language) -> InstructionSourceGenerator:
        match lang:
            case Language.PYTHON:
                return PythonInstructionSourceGenerator()

            case _:
                raise ValueError(f"Unknown lang option: {lang}")

    @staticmethod
    def getArgumentValidName(arg: EnvironmentInstructionArgument) -> str:
        if arg.pointing_type is None:
            return f"{arg.primitive_type.name}"
        return f"{arg.pointing_type.name}_ptr"

    def getInstructionFuncName(self, i: EnvironmentInstruction) -> str:
        args = "__".join(self.getArgumentValidName(a) for a in i.arguments)
        ret = f"__{i.parent}_{i.package}_{i.name}__{args}"
        self.instruction_names.append(ret)
        return ret

    def __init__(self):
        self.primitives: Optional[PrimitivesRegistry] = None
        self.instruction_names = list[str]()

    def run(self, env: Environment, primitives: PrimitivesRegistry, output_folder: Path) -> Path:
        self.primitives = primitives

        output_filepath = output_folder / f"{env.name}.{self.getFileExtension()}"

        with open(output_filepath, "w") as f:
            f.write(self.getFileHeadedLines(env))

            for i in env.instructions.values():
                f.write(self.process(i))

            f.write(f"INSTRUCTIONS = {ReprTool.iter(self.instruction_names)}\n")

        return output_filepath

    @abstractmethod
    def process(self, instruction: EnvironmentInstruction) -> str:
        """Обработать инструкцию и вывести её source код"""

    @abstractmethod
    def getFileExtension(self) -> str:
        """Получить расширение файла исходного кода"""

    @abstractmethod
    def getFileHeadedLines(self, env: Environment) -> str:
        """Текст начала файла"""


class PythonInstructionSourceGenerator(InstructionSourceGenerator):

    def getFileHeadedLines(self, env: Environment) -> str:
        enf_info = f"env: '{env.name}' from {env.parent!r}"
        return f"{self.docStr(enf_info)}\nfrom {Interpreter.__module__.__str__()} import {Interpreter.__name__}\n\n\n"

    def getFileExtension(self) -> str:
        return "py"

    def __init__(self):
        super().__init__()
        self.gs = GenerationSettings(
            vm_instance="vm",
            vm_class=Interpreter.__name__,
            vm_method_ipReadPrimitive="ipReadPrimitive",
            vm_method_ipReadHeapPointer="ipReadHeapPointer"
        )

    def processArgStatement(self, i: int, arg: EnvironmentInstructionArgument) -> str:
        if arg.pointing_type is None:
            return f"const_{arg.primitive_type.name}_{i} = {self.gs.vm_instance}.{self.gs.vm_method_ipReadPrimitive}({self.gs.vm_instance}.{arg.primitive_type.name})"
        else:
            return f"var_{arg.pointing_type.name}_{i} = {self.gs.vm_instance}.{self.gs.vm_method_ipReadHeapPointer}()"

    def process(self, instruction: EnvironmentInstruction) -> str:
        lines = (
            self.processArgStatement(index, arg)
            for index, arg in enumerate(instruction.arguments)
        )

        return self.pythonFunc(
            self.getInstructionFuncName(instruction),
            ((self.gs.vm_instance, self.gs.vm_class),),
            lines,
            "None",
            instruction.__repr__()
        )

    @staticmethod
    def pyLine(__s: str) -> str:
        return f"    {__s}\n"

    @staticmethod
    def docStr(__s: str) -> str:
        return f'"""{__s}"""'

    @classmethod
    def pythonFunc(cls, name: str, args: Iterable[tuple[str, str]], lines: Iterable[str], ret_t: str, doc: str) -> str:
        args_s = ", ".join(f"{__n}: {__t}" for __n, __t in args)
        declare = f"def {name}({args_s}) -> {ret_t}:\n"
        body = "".join(map(cls.pyLine, lines))
        doc_line = cls.pyLine(cls.docStr(doc))
        return f"{declare}{doc_line}{body}\n\n"

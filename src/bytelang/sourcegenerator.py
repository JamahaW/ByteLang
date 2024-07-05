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
from bytelang.content import PrimitiveType
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

    def strCall_ipReadPrimitive(self, primitive: PrimitiveType) -> str:
        return f"{self.vm_instance}.{self.vm_method_ipReadPrimitive}({self.vm_instance}.{primitive.name})"

    def strCall_ipReadHeapPointer(self) -> str:
        return f"{self.vm_instance}.{self.vm_method_ipReadHeapPointer}()"


class InstructionSourceGenerator(ABC):

    @staticmethod
    def create(lang: Language) -> InstructionSourceGenerator:
        match lang:
            case Language.PYTHON:
                return PythonInstructionSourceGenerator()

            case _:
                raise ValueError(lang)

    def _processInstructionName(self, instruction: EnvironmentInstruction) -> str:
        self.instruction_names.append(ret := instruction.reprShakeCase())
        return ret

    def __init__(self):
        self.primitives: Optional[PrimitivesRegistry] = None
        self.instruction_names = list[str]()

    def run(self, env: Environment, primitives: PrimitivesRegistry, output_folder: Path) -> Path:
        self.primitives = primitives
        output_filepath = output_folder / f"{env.name}.{self._getSourceExtension()}"

        with open(output_filepath, "w") as f:
            f.write(self._getFileHeadedLines(env))

            for instruction in env.instructions.values():
                f.write(self._process(instruction))

            f.write(self._getInstructionCollectionDeclare())

        return output_filepath

    @abstractmethod
    def _process(self, instruction: EnvironmentInstruction) -> str:
        """Обработать инструкцию и вывести её source код"""

    @abstractmethod
    def _getSourceExtension(self) -> str:
        """Расширение файла исходного кода"""

    @abstractmethod
    def _getFileHeadedLines(self, env: Environment) -> str:
        """Текст начала файла"""

    @abstractmethod
    def _getInstructionCollectionDeclare(self) -> str:
        """Сформировать выражение объявления коллекции инструкций"""


@dataclass(frozen=True)
class PythonSourceFunctionArgument:
    name: str
    annotation: Optional[str] = None

    def __repr__(self) -> str:
        if self.annotation is None:
            return self.name
        return f"{self.name}: {self.annotation}"


class PythonSourceGenerator:
    @staticmethod
    def intendLine(__s: str) -> str:
        return f"    {__s}\n"

    @staticmethod
    def docString(__s: str) -> str:
        return f'"""{__s}"""\n'

    @staticmethod
    def importClass(__cls: type) -> str:
        return f"from {__cls.__module__.__str__()} import {__cls.__name__}\n"

    @classmethod
    def pythonFunc(cls, name: str, args: Iterable[PythonSourceFunctionArgument], lines: Iterable[str], /, *, returns: str = None, doc_string: str = None) -> str:
        declare = f"def {name}{ReprTool.iter(args)} -> {returns}:\n"
        doc_string = '' if doc_string is None else cls.intendLine(cls.docString(doc_string))
        return f"{declare}{doc_string}{''.join(map(cls.intendLine, lines))}\n\n"


class PythonInstructionSourceGenerator(InstructionSourceGenerator, PythonSourceGenerator):

    def _getInstructionCollectionDeclare(self) -> str:
        return f"INSTRUCTIONS = {ReprTool.iter(self.instruction_names)}\n"

    def _getFileHeadedLines(self, env: Environment) -> str:
        enf_info = f"env: '{env.name}' from {env.parent!r}"
        return f"{self.docString(enf_info)}{self.importClass(Interpreter)}\n\n"

    def _getSourceExtension(self) -> str:
        return "py"

    def __init__(self):
        super().__init__()
        self.gs = GenerationSettings(
            vm_instance="vm",
            vm_class=Interpreter.__name__,
            vm_method_ipReadPrimitive="ipReadPrimitive",
            vm_method_ipReadHeapPointer="ipReadHeapPointer"
        )

    def __processArgStatement(self, i: int, arg: EnvironmentInstructionArgument) -> str:
        rv = self.gs.strCall_ipReadPrimitive(arg.primitive_type) if arg.pointing_type is None else self.gs.strCall_ipReadHeapPointer()
        return f"{arg.reprShakeCase()}_{i} = {rv}"

    def _process(self, instruction: EnvironmentInstruction) -> str:
        return self.pythonFunc(
            self._processInstructionName(instruction),
            (
                PythonSourceFunctionArgument(self.gs.vm_instance, self.gs.vm_class),
            ),
            (
                self.__processArgStatement(index, arg)
                for index, arg in enumerate(instruction.arguments)
            ),
            doc_string=instruction.__repr__()
        )

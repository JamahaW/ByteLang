from __future__ import annotations

from os import PathLike
from pathlib import Path
from typing import Optional

from bytelang.content import Environment
from bytelang.handlers import ErrorHandler
from bytelang.interpreters import Interpreter
from bytelang.processors import CompileResult
from bytelang.processors import Compiler
from bytelang.registries import EnvironmentsRegistry
from bytelang.registries import PackageRegistry
from bytelang.registries import PrimitivesRegistry
from bytelang.registries import ProfileRegistry
from bytelang.sourcegenerator import InstructionSourceGenerator
from bytelang.sourcegenerator import Language


class ByteLang:
    """API byteLang"""

    # TODO декомпиляция
    # TODO REPL режим

    def __init__(self) -> None:
        self.primitives_registry = PrimitivesRegistry()
        self.profile_registry = ProfileRegistry("json", self.primitives_registry)
        self.package_registry = PackageRegistry("blp", self.primitives_registry)
        self.environment_registry = EnvironmentsRegistry("json", self.profile_registry, self.package_registry)
        self.__errors_handler = ErrorHandler()
        self.__compiler = Compiler(self.__errors_handler, self.primitives_registry, self.environment_registry)

    def compile(self, source_filepath: PathLike | str, bytecode_filepath: PathLike | str) -> Optional[CompileResult]:
        """Скомпилировать исходный код bls в байткод программу"""
        self.__errors_handler.reset()
        return self.__compiler.run(source_filepath, bytecode_filepath)

    def decompile(self, env: str, bytecode_filepath: PathLike | str, source_filepath: PathLike | str) -> None:
        """Декомпилировать байткод с данной средой ВМ и сгенерировать исходный код"""
        pass

    def getErrorsLog(self) -> str:
        return self.__errors_handler.getLog()

    def generateSource(self, env: str, output_folder: PathLike | str, lang: Language = Language.PYTHON) -> Path:
        return InstructionSourceGenerator.create(lang).run(
            self.environment_registry.get(env),
            self.primitives_registry,
            Path(output_folder)
        )

# code_validation.py
import re
import sys
import tempfile
import ast
from typing import Tuple


from pylint.lint import PyLinter
from black import format_str, FileMode
from pathlib import Path

from stdlib_list import stdlib_list

from components.config import config


class CodeValidator:
    @staticmethod
    def extract_code_blocks(text: str) -> list[Tuple[str | None, str]] | None:
        recognized_languages = config.RECOGNIZED_LANGUAGES
        pattern = rf"```({'|'.join(recognized_languages)})?\n?([\s\S]*?)```"
        code_blocks = re.findall(pattern, text)
        if not code_blocks:
            return None
        return [
            (block[0] if block[0] else None, "\n".join(block[1].strip().split("\n")))
            for block in code_blocks
        ]

    @staticmethod
    def extract_python_imports(code: str) -> set[str]:
        try:
            standard_libs = set(
                stdlib_list(
                    version=f"{sys.version_info.major}.{sys.version_info.minor}"
                )
            )
            tree = ast.parse(code)
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update([name.name for name in node.names])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:  # Check if the module is not None
                        imports.add(node.module)
            non_standard_libs = imports - standard_libs
            return non_standard_libs
        except SyntaxError:
            # Handle invalid Python code
            return set()

    @staticmethod
    def is_valid_python(code: str) -> bool:
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    @staticmethod
    def format_with_black(code: str) -> str:
        return format_str(code, mode=FileMode())

    @staticmethod
    def run_pylint_static_analysis(code: str) -> tuple[int, int, list[str]]:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".py", mode="w"
        ) as temp_file:
            temp_file.write(code)
            temp_file_path = Path(temp_file.name)

        linter = PyLinter()
        linter.set_option("disable", config.PYLINT_DISABLED_CHECKS)

        linter.check([str(temp_file_path)])

        error_count = linter.stats.by_msg.get("E", 0)
        warning_count = linter.stats.by_msg.get("W", 0)
        messages = [str(msg) for msg in linter.reporter.messages]

        temp_file_path.unlink()
        return error_count, warning_count, messages

from pathlib import Path
from typing import TYPE_CHECKING

from .java_runner import JavaRunner
from .python_runner import PythonRunner

if TYPE_CHECKING:
    from .runner import CodeRunner

EXTENSION_MAP = {
    ".py": PythonRunner,
    ".java": JavaRunner,
}

LANGUAGE_MAP = {
    ".py": "python",
    ".java": "java",
}


def runner_for(src_file: str) -> CodeRunner:
    ext = Path(src_file).suffix.lower()
    cls = EXTENSION_MAP.get(ext)
    if cls is None:
        supported = ", ".join(EXTENSION_MAP)
        raise ValueError(f"Unsupported file extension '{ext}'. Supported: {supported}")
    return cls()


def get_language_for(src_file: str) -> str:
    ext = Path(src_file).suffix.lower()
    language = LANGUAGE_MAP.get(ext)
    if language is None:
        supported = ", ".join(LANGUAGE_MAP)
        raise ValueError(f"Unsupported file extension '{ext}'. Supported: {supported}")
    return language

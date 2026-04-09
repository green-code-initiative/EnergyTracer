from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from .runner import CodeRunner


class JavaRunner(CodeRunner):
    def __init__(self):
        self._tmpdir: tempfile.TemporaryDirectory | None = None
        self._java_path: str | None = None
        self._qualified_class_name_cache: str | None = None

    @property
    def language(self) -> str:
        return "java"

    @staticmethod
    def _package_name(code: str) -> str | None:
        package_match = re.search(
            r"^\s*package\s+([A-Za-z_][\w.]*)\s*;", code, re.MULTILINE
        )
        if package_match is None:
            return None
        return package_match.group(1)

    @staticmethod
    def _class_name(code: str) -> str:
        class_match = re.search(
            r"^\s*public\s+class\s+([A-Za-z_][A-Za-z0-9_]*)\s*", code, re.MULTILINE
        )
        if class_match is None:
            raise ValueError("Java source must declare a public class.")
        return class_match.group(1)

    def _qualified_class_name(self, code: str) -> str:
        package_name = self._package_name(code)
        class_name = self._class_name(code)
        if package_name is None:
            return class_name
        return f"{package_name}.{class_name}"

    def prepare(self, code: str) -> None:

        self.cleanup()

        package_name = self._package_name(code)
        class_name = self._class_name(code)
        javac = shutil.which("javac")
        java = shutil.which("java")
        if javac is None or java is None:
            raise RuntimeError("Java toolchain not found in PATH.")

        self._tmpdir = tempfile.TemporaryDirectory()
        tmp_path = Path(self._tmpdir.name)
        src_root = tmp_path
        if package_name is not None:
            src_root = src_root / package_name.replace(".", "/")
        src_root.mkdir(parents=True, exist_ok=True)

        src = src_root / f"{class_name}.java"
        src.write_text(code)
        subprocess.run([javac, str(src)], cwd=tmp_path, check=True)  # noqa: S603

        self._java_path = java
        self._qualified_class_name_cache = self._qualified_class_name(code)

    def run_prepared(self) -> None:
        if (
            self._tmpdir is None
            or self._java_path is None
            or self._qualified_class_name_cache is None
        ):
            raise RuntimeError("Java runner must be prepared before execution.")

        subprocess.run(  # noqa: S603
            [
                self._java_path,
                "-cp",
                self._tmpdir.name,
                self._qualified_class_name_cache,
            ],
            cwd=self._tmpdir.name,
            check=True,
        )

    def cleanup(self) -> None:
        if self._tmpdir is not None:
            self._tmpdir.cleanup()
        self._tmpdir = None
        self._java_path = None
        self._qualified_class_name_cache = None

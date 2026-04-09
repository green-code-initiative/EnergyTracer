from .runner import CodeRunner


class PythonRunner(CodeRunner):
    def __init__(self):
        self._code: str | None = None

    @property
    def language(self) -> str:
        return "python"

    def prepare(self, code: str) -> None:
        self._code = code

    def run_prepared(self) -> None:
        if self._code is None:
            raise RuntimeError("Python runner must be prepared before execution.")
        exec(self._code, {"__name__": "__main__"})

    def cleanup(self) -> None:
        self._code = None

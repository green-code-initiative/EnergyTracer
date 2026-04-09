from abc import ABC, abstractmethod


class CodeRunner(ABC):
    @abstractmethod
    def prepare(self, code: str) -> None:
        """Prepare the source code for repeated execution."""

    @abstractmethod
    def run_prepared(self) -> None:
        """Execute one iteration using already-prepared artifacts."""

    @abstractmethod
    def cleanup(self) -> None:
        """Release temporary resources created during prepare()."""

    @property
    @abstractmethod
    def language(self) -> str:
        """Human-readable language name, used for logging."""

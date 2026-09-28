from abc import ABC, abstractmethod


class DocWriter(ABC):
    """Abstract base class defining a document writer interface.

    Subclasses implement each method to produce output in a specific markup
    format (e.g. Markdown, AsciiDoc).

    Content is accumulated in the internal ``_report_content`` list via the
    ``add_*`` methods.  The ``get_*`` helpers return formatted strings without
    appending them, so they can be embedded inside other content.  Call
    :meth:`build` to join all accumulated fragments into a single string.
    """

    def __init__(self):
        self._report_content: list[str] = []

    @abstractmethod
    def add_code_block(self, language: str, code: str) -> None:
        """Append a code block with syntax highlighting.

        Args:
            language: Language identifier for syntax highlighting (e.g. ``"python"``).
            code: The source code to display.
        """

    @abstractmethod
    def add_h1(self, title: str) -> None:
        """Append a level-1 heading."""

    @abstractmethod
    def add_h2(self, title: str) -> None:
        """Append a level-2 heading."""

    @abstractmethod
    def add_h3(self, title: str) -> None:
        """Append a level-3 heading."""

    @abstractmethod
    def add_h4(self, title: str) -> None:
        """Append a level-4 heading."""

    @abstractmethod
    def add_image(self, path: str, alt: str) -> None:
        """Append an image reference.

        Args:
            path: Path to the image file.
            alt: Alternative text for the image.
        """

    @abstractmethod
    def add_inline_code(self, code: str) -> None:
        """Append an inline code span to the report content."""

    @abstractmethod
    def add_line_break(self) -> None:
        """Append a horizontal rule / thematic break."""

    @abstractmethod
    def add_link(self, url: str, title: str) -> None:
        """Append a hyperlink.

        Args:
            url: The target URL.
            title: The visible link text.
        """

    @abstractmethod
    def add_list(self, elements: list) -> None:
        """Append an unordered list.

        Args:
            elements: Items to render, one per bullet.
        """

    @abstractmethod
    def add_newline(self) -> None:
        """Append a blank line."""

    @abstractmethod
    def add_paragraph(self, text: str) -> None:
        """Append a paragraph of text."""

    @abstractmethod
    def add_quote(self, text: str) -> None:
        """Append a blockquote."""

    @abstractmethod
    def add_table(self, head: list[list], table_rows: list[list]) -> None:
        """Append a table.

        Args:
            head: A list containing a single list of column header labels.
                    Can also contain alignement for markdown table (L : left, R : right, C : center).
            table_rows: A list of rows, where each row is a list of cell values.
        """

    def build(self) -> str:
        """Join all accumulated content fragments and return the full document."""
        return "".join(self._report_content)

    @abstractmethod
    def get_bold(self, text: str) -> str:
        """Return *text* with bold formatting applied."""

    @abstractmethod
    def get_highlight(self, text: str) -> str:
        """Return *text* with highlight formatting applied."""

    @abstractmethod
    def get_inline_code(self, code: str) -> str:
        """Return *code* as an inline code span."""

    @abstractmethod
    def get_italic(self, text: str) -> str:
        """Return *text* with italic formatting applied."""

from .doc_writer import DocWriter


class AsciidocWriter(DocWriter):

    def __init__(self):
        super().__init__()

    def add_code_block(self, language: str, code: str) -> None:
        code_block: str = f"[source,{language}]\n"
        code_block += "----\n"
        code_block += code
        code_block += "\n----\n"
        self._report_content.append(code_block)

    def add_h1(self, title: str) -> None:
        self._report_content.append(f"\n= {title}\n")

    def add_h2(self, title: str) -> None:
        self._report_content.append(f"\n== {title}\n")

    def add_h3(self, title: str) -> None:
        self._report_content.append(f"\n=== {title}\n")

    def add_h4(self, title: str) -> None:
        self._report_content.append(f"\n==== {title}\n")

    def add_image(self, path: str, alt: str) -> None:
        self._report_content.append(f"image:{path}[{alt}]")

    def add_inline_code(self, code: str) -> None:
        self._report_content.append(f"`{code}`")

    def add_line_break(self) -> None:
        self._report_content.append("\n'''\n\n")

    def add_link(self, url: str, title: str) -> None:
        self._report_content.append(f"{url}[{title}]")

    def add_list(self, elements: list) -> None:
        for text in elements:
            self._report_content.append(f"* {text}\n")

    def add_newline(self) -> None:
        self._report_content.append("\n")

    def add_paragraph(self, text: str) -> None:
        self._report_content.append(f"{text}\n\n")

    def add_quote(self, text: str) -> None:
        self._report_content.append(f"[quote]\n{text}\n")

    def add_table(self, head: list[list], table_rows: list[list]) -> None:
        table = "|===\n"
        for cell in head[0]:
            table += f"| {cell}"
        table += "\n\n"
        for row in table_rows:
            for cell in row:
                table += f"| {cell} "
            table += "\n"
        table += "|===\n"
        self._report_content.append(table)

    def get_bold(self, text: str) -> str:
        return f"**{text}**"

    def get_highlight(self, text: str) -> str:
        return f"#{text}#"

    def get_inline_code(self, code: str) -> str:
        return f"`{code}`"

    def get_italic(self, text: str) -> str:
        return f"_{text}_"

"""Tests for docs.convert_readme_to_index_html.

These tests validate that our Markdown → HTML conversion:

- Wraps content in a full HTML document with our standard styling
- Maps core Markdown constructs to expected HTML structures
- Creates parent directories for the output file when needed

We import the script from the `docs/` directory to exercise the public
function instead of shelling out, keeping tests fast and deterministic.
"""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

import pytest


def _import_converter():
    """Dynamically import the converter module from `docs/`.

    Returns
    -------
    module
        The imported `convert_readme_to_index_html` module.
    """
    docs_dir = Path("docs").resolve()
    if str(docs_dir) not in sys.path:
        sys.path.insert(0, str(docs_dir))
    # Import locally; tests assume repository root as CWD
    import importlib

    return importlib.import_module("convert_readme_to_index_html")


@pytest.mark.parametrize(
    "md_text",
    [
        dedent(
            """
            # Sample Title

            This is a paragraph with an [inline link](https://example.com), an image ![alt text](imgs/pic.png), and **bold** with *italic*.

            - item one
            - item two

            1. first
            2. second

            ```python
            print("hello world")
            ```

            ---

            ## Subsection

            Some more text with `inline code`.
            > A quoted line.
            """
        )
    ],
)
def test_convert_basic_html_structure(tmp_path: Path, md_text: str) -> None:
    """End-to-end conversion produces a styled, complete HTML page.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary directory for isolated I/O.
    md_text : str
        Markdown content to render.
    """
    converter = _import_converter()

    md_file = tmp_path / "README.md"
    out_file = tmp_path / "public" / "index.html"
    md_file.write_text(md_text, encoding="utf-8")

    # Act
    converter.convert_md_to_html(str(md_file), str(out_file))

    # Assert: output exists and parent directories created
    assert out_file.exists(), "Output HTML file was not created"

    html = out_file.read_text(encoding="utf-8")

    # Minimal document shape
    assert "<!DOCTYPE html>" in html
    assert "<html" in html and "</html>" in html
    assert "<head>" in html and "</head>" in html
    assert "<body>" in html and "</body>" in html

    # Our house CSS and container wrapper
    assert ".container" in html
    assert '<div class="container">' in html

    # Headings, lists, code blocks, and links
    assert "<h1" in html and "Sample Title" in html
    assert "<h2" in html and "Subsection" in html
    assert "<ul>" in html and "<li>item one</li>" in html
    assert "<ol>" in html and "<li>first</li>" in html
    assert '<a href="https://example.com"' in html
    assert '<img src="imgs/pic.png" alt="alt text"' in html
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html

    # Code fences render as highlighted blocks or preformatted code
    assert ("codehilite" in html) or ("<pre><code" in html)

    # Horizontal rule mapping
    assert "<hr" in html

    # Blockquote mapping
    assert "<blockquote>" in html


def test_cli_parent_directories_created(tmp_path: Path) -> None:
    """Conversion creates parent directories for the output file.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory provided by pytest.
    """
    converter = _import_converter()

    md_file = tmp_path / "README.md"
    md_file.write_text("# Title", encoding="utf-8")
    out_file = tmp_path / "nested" / "deeper" / "index.html"

    converter.convert_md_to_html(str(md_file), str(out_file))

    assert out_file.exists(), "Converter did not create nested output path"


def test_convert_advanced_markdown(tmp_path: Path) -> None:
    """Advanced Markdown constructs: tables, footnotes, strikethrough, task lists.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory provided by pytest.
    """
    converter = _import_converter()

    md = dedent(
        """
        ## Data Table

        | Col A | Col B |
        |:-----:|------:|
        | a1    | b1    |
        | a2    | b2    |

        Text with footnote ref[^n1] and ~~strikethrough~~.

        - [x] done item
        - [ ] todo item

        [^n1]: This is the first footnote.
        """
    )
    md_file = tmp_path / "README.md"
    out_file = tmp_path / "index.html"
    md_file.write_text(md, encoding="utf-8")

    converter.convert_md_to_html(str(md_file), str(out_file))

    html = out_file.read_text(encoding="utf-8")

    # Table structure and alignment
    assert "<table" in html and "</table>" in html
    assert "<thead>" in html and "<tbody>" in html
    # alignment attributes present
    assert "text-align:center" in html or "text-align: center" in html
    assert "text-align:right" in html or "text-align: right" in html

    # Footnotes section contains our note
    assert "Footnotes" in html
    assert "This is the first footnote." in html
    # Reference rendered as sup link
    assert "fnref:n1" in html and "fn:n1" in html

    # Strikethrough
    assert "<del>strikethrough</del>" in html

    # Task list checkboxes
    assert '<input type="checkbox" disabled checked' in html
    assert '<input type="checkbox" disabled' in html


def test_nested_lists_render(tmp_path: Path) -> None:
    """Nested unordered and ordered lists render into nested list structures.

    We assert presence of nested list tags and items at multiple levels.
    """
    converter = _import_converter()

    md = dedent(
        """
        - level 1
          - level 2
            - level 3
        - sibling 1

        1. one
           1. one.one
        2. two
        """
    )
    md_file = tmp_path / "README.md"
    out_file = tmp_path / "index.html"
    md_file.write_text(md, encoding="utf-8")

    converter.convert_md_to_html(str(md_file), str(out_file))
    html = out_file.read_text(encoding="utf-8")

    # Multiple list containers appear
    assert html.count("<ul>") >= 2
    assert html.count("<ol>") >= 1
    # Items present
    assert "level 2" in html and "level 3" in html
    assert "one.one" in html


def test_table_cell_escaping(tmp_path: Path) -> None:
    """Escaped pipes within table cells are preserved as literal characters.

    Also preserves escaped backslashes.
    """
    converter = _import_converter()

    md = dedent(
        r"""
        | A | B |
        |---|---|
        | a\|1 | b\\2 |
        """
    )
    md_file = tmp_path / "README.md"
    out_file = tmp_path / "index.html"
    md_file.write_text(md, encoding="utf-8")

    converter.convert_md_to_html(str(md_file), str(out_file))
    html = out_file.read_text(encoding="utf-8")

    assert "<table" in html
    assert "a|1" in html
    assert "b\\2" in html

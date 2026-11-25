"""A tiny document model rendered to HTML, DOCX and PDF.

Inline markup supported in text: **bold**, *italic*, `code`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Heading:
    text: str
    level: int = 1


@dataclass
class Para:
    text: str
    style: str = "normal"  # normal | small | note | pending | warning | title | subtitle | center


@dataclass
class Bullets:
    items: list[str]
    ordered: bool = False


@dataclass
class Table:
    head: list[str]
    rows: list[list[str]]
    caption: str | None = None
    widths: list[float] | None = None  # relative widths


@dataclass
class Figure:
    path: Path
    caption: str
    width_frac: float = 0.9


@dataclass
class Code:
    text: str


@dataclass
class PageBreak:
    pass


Block = Heading | Para | Bullets | Table | Figure | Code | PageBreak


@dataclass
class Document:
    title: str
    blocks: list = field(default_factory=list)
    watermark: str | None = None

    def add(self, *blocks) -> "Document":
        for b in blocks:
            if isinstance(b, list):
                self.blocks.extend(b)
            elif b is not None:
                self.blocks.append(b)
        return self

    def h(self, text: str, level: int = 1) -> None:
        self.blocks.append(Heading(text, level))

    def p(self, text: str, style: str = "normal") -> None:
        self.blocks.append(Para(text, style))


INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`)")


def runs(text: str) -> list[tuple[str, bool, bool, bool]]:
    """Split inline markup into (text, bold, italic, code) runs."""
    out = []
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            out.append((part[2:-2], True, False, False))
        elif part.startswith("`") and part.endswith("`"):
            out.append((part[1:-1], False, False, True))
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            out.append((part[1:-1], False, True, False))
        else:
            out.append((part, False, False, False))
    return out


# ---------------------------------------------------------------------------
# Minimal Markdown → blocks (headings, paragraphs, lists, tables, code)
# ---------------------------------------------------------------------------

def from_markdown(md: str, base_level: int = 1, drop_sections: tuple[str, ...] = (), skip_first_h1: bool = True) -> list:
    lines = md.splitlines()
    blocks: list = []
    i = 0
    para: list[str] = []
    skipping_level: int | None = None
    first_h1_seen = False

    def flush():
        if para:
            blocks.append(Para(" ".join(s.strip() for s in para)))
            para.clear()

    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush()
            lvl = len(m.group(1))
            text = m.group(2).strip()
            if skipping_level is not None and lvl <= skipping_level:
                skipping_level = None
            if any(text.lower().startswith(d.lower()) for d in drop_sections):
                skipping_level = lvl
                i += 1
                continue
            if skipping_level is None:
                if lvl == 1 and skip_first_h1 and not first_h1_seen:
                    first_h1_seen = True
                else:
                    blocks.append(Heading(text, min(4, max(1, lvl - 1 + base_level - (1 if skip_first_h1 else 0)))))
            i += 1
            continue
        if skipping_level is not None:
            i += 1
            continue
        if line.startswith("```"):
            flush()
            j = i + 1
            code = []
            while j < len(lines) and not lines[j].startswith("```"):
                code.append(lines[j])
                j += 1
            blocks.append(Code("\n".join(code)))
            i = j + 1
            continue
        if line.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            flush()
            head = [c.strip() for c in line.strip().strip("|").split("|")]
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            blocks.append(Table(head, rows))
            i = j
            continue
        lm = re.match(r"^\s*([-*]|\d+\.)\s+(.*)$", line)
        if lm:
            flush()
            ordered = lm.group(1)[0].isdigit()
            items = []
            j = i
            while j < len(lines):
                mm = re.match(r"^\s*([-*]|\d+\.)\s+(.*)$", lines[j])
                if mm:
                    items.append(mm.group(2).strip())
                elif lines[j].startswith("  ") and lines[j].strip() and items:
                    items[-1] += " " + lines[j].strip()
                else:
                    break
                j += 1
            blocks.append(Bullets(items, ordered))
            i = j
            continue
        if line.startswith(">"):
            flush()
            blocks.append(Para(line.lstrip("> ").strip(), "note"))
            i += 1
            continue
        if not line.strip():
            flush()
        else:
            para.append(line)
        i += 1
    flush()
    return blocks

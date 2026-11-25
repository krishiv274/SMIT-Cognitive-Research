"""Render a :class:`Document` to HTML, DOCX (python-docx) and PDF (ReportLab)."""
from __future__ import annotations

import base64
import html
from pathlib import Path

from .document import Bullets, Code, Document, Figure, Heading, PageBreak, Para, Table, runs

# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

CSS = """
body{font-family:Georgia,'Times New Roman',serif;max-width:900px;margin:40px auto;padding:0 20px;line-height:1.55;color:#111;background:#fff}
h1,h2,h3,h4{font-family:system-ui,-apple-system,'Segoe UI',Arial,sans-serif;line-height:1.25}
h1{font-size:1.7em;border-bottom:2px solid #1F3A93;padding-bottom:.2em;margin-top:2em}
h2{font-size:1.3em;margin-top:1.6em}h3{font-size:1.1em}
table{border-collapse:collapse;width:100%;margin:1em 0;font-size:.88em;font-family:system-ui,Arial,sans-serif}
th,td{border:1px solid #bbb;padding:4px 6px;vertical-align:top;text-align:left}th{background:#e8ecf6}
caption{caption-side:top;text-align:left;font-weight:bold;padding:4px 0}
figure{margin:1.2em 0;text-align:center}figure img{max-width:100%}figcaption{font-size:.9em;color:#333;text-align:left}
.note{background:#eef3fb;border-left:4px solid #1F3A93;padding:8px 12px}.pending{background:#fff4e0;border-left:4px solid #e69f00;padding:8px 12px;font-style:italic}
.warning{background:#fdecea;border-left:4px solid #c00;padding:8px 12px}.small{font-size:.85em;color:#444}
.title{font-size:2em;font-weight:bold;text-align:center;font-family:system-ui,Arial,sans-serif;margin-top:2em}.subtitle{text-align:center;font-size:1.1em}.center{text-align:center}
pre{background:#f5f5f5;padding:10px;overflow:auto;font-size:.8em}
.watermark{position:fixed;top:8px;right:12px;background:#e69f00;color:#fff;padding:4px 10px;font:bold 12px Arial;border-radius:4px}
@media print{.watermark{position:static}}
"""


def _inline_html(text: str) -> str:
    out = []
    for t, b, i, c in runs(text):
        s = html.escape(t)
        if c:
            s = f"<code>{s}</code>"
        if b:
            s = f"<strong>{s}</strong>"
        if i:
            s = f"<em>{s}</em>"
        out.append(s)
    return "".join(out)


def to_html(doc: Document, path: Path) -> Path:
    parts = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>{html.escape(doc.title)}</title>",
             f"<meta name='viewport' content='width=device-width,initial-scale=1'><style>{CSS}</style></head><body>"]
    if doc.watermark:
        parts.append(f"<div class='watermark'>{html.escape(doc.watermark)}</div>")
    for b in doc.blocks:
        if isinstance(b, Heading):
            lvl = min(4, b.level)
            parts.append(f"<h{lvl}>{_inline_html(b.text)}</h{lvl}>")
        elif isinstance(b, Para):
            cls = "" if b.style == "normal" else f" class='{b.style}'"
            parts.append(f"<p{cls}>{_inline_html(b.text)}</p>")
        elif isinstance(b, Bullets):
            tag = "ol" if b.ordered else "ul"
            parts.append(f"<{tag}>" + "".join(f"<li>{_inline_html(x)}</li>" for x in b.items) + f"</{tag}>")
        elif isinstance(b, Table):
            cap = f"<caption>{_inline_html(b.caption)}</caption>" if b.caption else ""
            head = "".join(f"<th>{_inline_html(h)}</th>" for h in b.head)
            rows = "".join("<tr>" + "".join(f"<td>{_inline_html(str(c))}</td>" for c in r) + "</tr>" for r in b.rows)
            parts.append(f"<table>{cap}<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>")
        elif isinstance(b, Figure):
            if b.path.exists():
                data = base64.b64encode(b.path.read_bytes()).decode()
                parts.append(f"<figure><img alt='{html.escape(b.caption)}' src='data:image/png;base64,{data}'>"
                             f"<figcaption>{_inline_html(b.caption)}</figcaption></figure>")
        elif isinstance(b, Code):
            parts.append(f"<pre>{html.escape(b.text)}</pre>")
        elif isinstance(b, PageBreak):
            parts.append("<div style='page-break-after:always'></div>")
    parts.append("</body></html>")
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------

def to_docx(doc: Document, path: Path) -> Path:
    from docx import Document as Docx
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor

    d = Docx()
    st = d.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(11)
    sec = d.sections[0]
    sec.left_margin = sec.right_margin = Inches(1)
    if doc.watermark:
        hp = sec.header.paragraphs[0]
        r = hp.add_run(doc.watermark)
        r.bold = True
        r.font.color.rgb = RGBColor(0xB3, 0x59, 0x00)

    def add_runs(par, text, size=None, color=None):
        for t, b, i, c in runs(text):
            r = par.add_run(t)
            r.bold = b or None
            r.italic = i or None
            if c:
                r.font.name = "Consolas"
            if size:
                r.font.size = Pt(size)
            if color:
                r.font.color.rgb = color

    def shade(cell, hexcolor):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), hexcolor)
        tcPr.append(shd)

    for b in doc.blocks:
        if isinstance(b, Heading):
            h = d.add_heading(level=min(4, b.level))
            add_runs(h, b.text)
        elif isinstance(b, Para):
            p = d.add_paragraph()
            if b.style == "title":
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_runs(p, b.text, 20)
                p.runs[0].bold = True if p.runs else None
            elif b.style in ("subtitle", "center"):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_runs(p, b.text, 13 if b.style == "subtitle" else None)
            elif b.style == "pending":
                add_runs(p, b.text, color=RGBColor(0xB3, 0x59, 0x00))
                for r in p.runs:
                    r.italic = True
            elif b.style == "warning":
                add_runs(p, b.text, color=RGBColor(0xC0, 0x00, 0x00))
            elif b.style in ("note", "small"):
                add_runs(p, b.text, 9.5 if b.style == "small" else None, RGBColor(0x1F, 0x3A, 0x93) if b.style == "note" else None)
            else:
                add_runs(p, b.text)
        elif isinstance(b, Bullets):
            for it in b.items:
                p = d.add_paragraph(style="List Number" if b.ordered else "List Bullet")
                add_runs(p, it)
        elif isinstance(b, Table):
            if b.caption:
                cp = d.add_paragraph()
                add_runs(cp, b.caption)
                for r in cp.runs:
                    r.bold = True
            t = d.add_table(rows=1, cols=len(b.head))
            t.style = "Table Grid"
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            for j, h in enumerate(b.head):
                c = t.rows[0].cells[j]
                c.text = ""
                add_runs(c.paragraphs[0], h, 9)
                for r in c.paragraphs[0].runs:
                    r.bold = True
                shade(c, "E8ECF6")
            for row in b.rows:
                cells = t.add_row().cells
                for j, v in enumerate(row[: len(b.head)]):
                    cells[j].text = ""
                    add_runs(cells[j].paragraphs[0], str(v), 9)
            d.add_paragraph()
        elif isinstance(b, Figure):
            if b.path.exists():
                d.add_picture(str(b.path), width=Inches(6.3 * b.width_frac))
                d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                cp = d.add_paragraph()
                add_runs(cp, b.caption, 9.5)
        elif isinstance(b, Code):
            p = d.add_paragraph()
            r = p.add_run(b.text)
            r.font.name = "Consolas"
            r.font.size = Pt(8)
        elif isinstance(b, PageBreak):
            d.add_page_break()
    d.core_properties.title = doc.title
    d.save(str(path))
    return path


# ---------------------------------------------------------------------------
# PDF (ReportLab, DejaVu fonts shipped with Matplotlib for full Unicode coverage)
# ---------------------------------------------------------------------------

_FONTS_REGISTERED = False


def _register_fonts() -> str:
    global _FONTS_REGISTERED
    from reportlab.lib.fonts import addMapping
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    if _FONTS_REGISTERED:
        return "DejaVuSans"
    import matplotlib

    fdir = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    pdfmetrics.registerFont(TTFont("DejaVuSans", str(fdir / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", str(fdir / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Oblique", str(fdir / "DejaVuSans-Oblique.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVuSans-BoldOblique", str(fdir / "DejaVuSans-BoldOblique.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVuSansMono", str(fdir / "DejaVuSansMono.ttf")))
    addMapping("DejaVuSans", 0, 0, "DejaVuSans")
    addMapping("DejaVuSans", 1, 0, "DejaVuSans-Bold")
    addMapping("DejaVuSans", 0, 1, "DejaVuSans-Oblique")
    addMapping("DejaVuSans", 1, 1, "DejaVuSans-BoldOblique")
    _FONTS_REGISTERED = True
    return "DejaVuSans"


def _inline_rl(text: str) -> str:
    out = []
    for t, b, i, c in runs(text):
        s = html.escape(t, quote=False)
        if c:
            s = f"<font face='DejaVuSansMono'>{s}</font>"
        if b:
            s = f"<b>{s}</b>"
        if i:
            s = f"<i>{s}</i>"
        out.append(s)
    return "".join(out)


def to_pdf(doc: Document, path: Path) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Image,
        KeepTogether,
        ListFlowable,
        ListItem,
        PageBreak as RLPageBreak,
        Paragraph,
        Preformatted,
        SimpleDocTemplate,
        Spacer,
        Table as RLTable,
        TableStyle,
    )

    font = _register_fonts()
    ss = getSampleStyleSheet()
    base = ParagraphStyle("base", parent=ss["Normal"], fontName=font, fontSize=10, leading=14, spaceAfter=6)
    styles = {
        "normal": base,
        "small": ParagraphStyle("small", parent=base, fontSize=8.5, leading=11, textColor=colors.HexColor("#444444")),
        "note": ParagraphStyle("note", parent=base, backColor=colors.HexColor("#EEF3FB"), borderPadding=5, leftIndent=4),
        "pending": ParagraphStyle("pending", parent=base, backColor=colors.HexColor("#FFF4E0"), borderPadding=5,
                                  textColor=colors.HexColor("#7A3D00")),
        "warning": ParagraphStyle("warning", parent=base, textColor=colors.HexColor("#B00000")),
        "title": ParagraphStyle("title", parent=base, fontSize=20, leading=26, alignment=TA_CENTER, spaceBefore=60, spaceAfter=20),
        "subtitle": ParagraphStyle("subtitle", parent=base, fontSize=12, leading=17, alignment=TA_CENTER),
        "center": ParagraphStyle("center", parent=base, alignment=TA_CENTER),
    }
    hstyles = {i: ParagraphStyle(f"h{i}", parent=base, fontName=font, fontSize={1: 16, 2: 13, 3: 11.5, 4: 10.5}[i],
                                 leading={1: 20, 2: 17, 3: 15, 4: 14}[i], spaceBefore={1: 14, 2: 10, 3: 8, 4: 6}[i],
                                 spaceAfter=6, textColor=colors.HexColor("#1F3A93") if i <= 2 else colors.black)
               for i in range(1, 5)}
    cell = ParagraphStyle("cell", parent=base, fontSize=7.8, leading=9.6, spaceAfter=0)
    cellh = ParagraphStyle("cellh", parent=cell, fontName=font)
    width = A4[0] - 4 * cm
    story = []
    for b in doc.blocks:
        if isinstance(b, Heading):
            story.append(Paragraph(f"<b>{_inline_rl(b.text)}</b>", hstyles[min(4, b.level)]))
        elif isinstance(b, Para):
            story.append(Paragraph(_inline_rl(b.text), styles.get(b.style, base)))
        elif isinstance(b, Bullets):
            story.append(ListFlowable([ListItem(Paragraph(_inline_rl(x), base), leftIndent=12) for x in b.items],
                                      bulletType="1" if b.ordered else "bullet", start="1" if b.ordered else None,
                                      leftIndent=14, bulletFontName=font))
        elif isinstance(b, Table):
            data = [[Paragraph(f"<b>{_inline_rl(h)}</b>", cellh) for h in b.head]]
            for r in b.rows:
                data.append([Paragraph(_inline_rl(str(c)), cell) for c in r[: len(b.head)]] +
                            [Paragraph("", cell)] * (len(b.head) - len(r[: len(b.head)])))
            if b.widths:
                tot = sum(b.widths)
                cw = [width * w / tot for w in b.widths]
            else:
                lens = [max(len(str(x)) for x in [h] + [r[j] if j < len(r) else "" for r in b.rows]) for j, h in enumerate(b.head)]
                lens = [min(max(l, 4), 60) for l in lens]
                cw = [width * l / sum(lens) for l in lens]
            t = RLTable(data, colWidths=cw, repeatRows=1)
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8ECF6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]))
            items = []
            if b.caption:
                items.append(Paragraph(f"<b>{_inline_rl(b.caption)}</b>", base))
            items.append(t)
            if len(b.rows) < 12:
                story.append(KeepTogether(items))
            else:
                story.extend(items)
            story.append(Spacer(1, 8))
        elif isinstance(b, Figure):
            if b.path.exists():
                from reportlab.lib.utils import ImageReader

                iw, ih = ImageReader(str(b.path)).getSize()
                w = width * b.width_frac
                h = w * ih / iw
                maxh = 19 * cm
                if h > maxh:
                    w, h = w * maxh / h, maxh
                story.append(KeepTogether([Image(str(b.path), width=w, height=h),
                                           Paragraph(_inline_rl(b.caption), styles["small"]), Spacer(1, 8)]))
        elif isinstance(b, Code):
            story.append(Preformatted(b.text, ParagraphStyle("code", parent=base, fontName="DejaVuSansMono", fontSize=6.8, leading=8.2)))
        elif isinstance(b, PageBreak):
            story.append(RLPageBreak())

    def on_page(canvas, d):
        canvas.saveState()
        canvas.setFont(font, 7.5)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(2 * cm, 1.2 * cm, doc.title[:110])
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {d.page}")
        if doc.watermark:
            canvas.setFillColor(colors.HexColor("#B35900"))
            canvas.setFont(font, 8)
            canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.2 * cm, doc.watermark)
        canvas.restoreState()

    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
                      title=doc.title, author="SMIT research team").build(story, onFirstPage=on_page, onLaterPages=on_page)
    return path

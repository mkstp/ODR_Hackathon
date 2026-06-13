#!/usr/bin/env python3
"""build_report.py — Generate branded two-pager PDF from a Markdown content file.

Usage (run from project root):
    python3 src/scripts/build_report.py docs/reports/two-pagers/<slug>/<slug>.md
    python3 src/scripts/build_report.py docs/reports/two-pagers/<slug>/<slug>.md --out build/<slug>.pdf

Content format: Markdown with YAML front-matter. Recognized section types:
    ## Lead          — thesis paragraph, rendered in lead style
    ## <Any heading> — body section with optional callout box
    ## Implication   — closing section, rendered in teal panel

Callout syntax (at most one per document, inside a body section):
    > **Label:** Highlighted claim or statistic.
"""

import os
import re
import sys
import yaml
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

# ── Page dimensions ───────────────────────────────────────────────────────────
PAGE_W, PAGE_H   = letter           # 612 × 792 pt
MARGIN           = 48
CONTENT_W        = PAGE_W - 2 * MARGIN   # 516 pt
LOGO_STRIP_H     = 34   # white band: colored logo lives here
TITLE_BAND_H     = 44   # dark teal band: title (+ optional subtitle)
HEADER_H         = LOGO_STRIP_H + TITLE_BAND_H   # total header height
MINI_HEADER_H    = 26
FOOTER_H         = 28

# ── Brand colors ──────────────────────────────────────────────────────────────
C_DARK_TEAL  = HexColor('#2E4057')
C_OLIVE      = HexColor('#E8863A')
C_BODY_GRAY  = HexColor('#595959')
C_LIGHT_GRAY = HexColor('#EFEFEF')
C_LIGHT_TEAL = HexColor('#ECF0F7')
C_WHITE      = HexColor('#FFFFFF')

# ── Type scale ────────────────────────────────────────────────────────────────
SZ_TITLE    = 18
SZ_SUBTITLE = 10
SZ_META     = 9
SZ_LEAD    = 10.5
SZ_SECTION = 12
SZ_BODY    = 10.5
SZ_FOOTER  = 8

LH_LEAD    = 15.0   # 10.5pt × 1.43 — unified with body
LH_BODY    = 15.0   # 10.5pt × 1.43
LH_SECTION = 17.0   # 12pt   × 1.41

FONT_REG  = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

PROJECT_ROOT  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LOGO_PATH     = os.path.join(PROJECT_ROOT, 'assets', 'images', 'logo.png')
LOGO_WHITE_PATH = os.path.join(PROJECT_ROOT, 'assets', 'images', 'logo_white.png')


# ── Font registration ─────────────────────────────────────────────────────────
def register_fonts():
    print('  Font: Helvetica')


# ── Text utilities ────────────────────────────────────────────────────────────
def wrap_text(c, text, font, size, max_width):
    """Wrap text to max_width. Returns list of line strings."""
    words = str(text).split()
    if not words:
        return ['']
    lines, line, line_w = [], [], 0
    sp_w = c.stringWidth(' ', font, size)
    for word in words:
        w = c.stringWidth(word, font, size)
        if line and line_w + sp_w + w > max_width:
            lines.append(' '.join(line))
            line, line_w = [word], w
        else:
            line_w += (sp_w if line else 0) + w
            line.append(word)
    if line:
        lines.append(' '.join(line))
    return lines


# ── Markdown parser ───────────────────────────────────────────────────────────
def parse_document(path):
    """Parse Markdown with YAML front-matter.

    Returns (meta: dict, blocks: list) where each block is one of:
      ('lead', text)
      ('section', header, text, callout_or_None)   callout = (label, body_text)
      ('implication', text)
    """
    with open(path, 'r') as fh:
        raw = fh.read()

    fm = re.match(r'^---\n(.*?)\n---\n', raw, re.DOTALL)
    if not fm:
        raise ValueError(f'No YAML front-matter found in {path}')
    meta = yaml.safe_load(fm.group(1))
    body = raw[fm.end():]

    # Accept colon inside bold (**Label:** body) or outside (**Label**: body)
    callout_re = re.compile(r'^\s*>\s*\*\*([^*:]+):?\*\*:?\s*(.+)$', re.MULTILINE)

    # Split on ## headers
    parts = re.split(r'(?m)^(?=## )', body.lstrip('\n'))
    blocks = []

    for part in parts:
        part = part.strip()
        if not part or not part.startswith('## '):
            continue
        first_nl = part.find('\n')
        if first_nl == -1:
            header, content = part[3:].strip(), ''
        else:
            header  = part[3:first_nl].strip()
            content = part[first_nl:].strip()

        # Extract callout
        callout = None
        cm = callout_re.search(content)
        if cm:
            callout = (cm.group(1).strip(), cm.group(2).strip())
            content = (content[:cm.start()] + content[cm.end():]).strip()

        h = header.lower()
        if h == 'lead':
            blocks.append(('lead', content))
        elif h in ('implication', 'implications'):
            blocks.append(('implication', content))
        else:
            blocks.append(('section', header, content, callout))

    return meta, blocks


# ── Renderer ──────────────────────────────────────────────────────────────────
class Renderer:
    def __init__(self, c, meta):
        self.c    = c
        self.meta = meta
        self.page = 0
        self.y    = 0
        self._start_page()

    # ── Page scaffolding ─────────────────────────────────────────────────────

    def _start_page(self):
        self.page += 1
        if self.page == 1:
            self._draw_main_header()
            self._draw_footer()
            meta_y = PAGE_H - HEADER_H - 16
            self._draw_meta_line(meta_y)
            self.y = meta_y - 22
        else:
            self._draw_continuation_header()
            self._draw_footer()
            self.y = PAGE_H - MINI_HEADER_H - MARGIN

    def _draw_main_header(self):
        c    = self.c
        title    = self.meta.get('title', 'Untitled')
        subtitle = self.meta.get('subtitle', '')

        # ── White logo strip (top) ──────────────────────────────────────────
        logo_strip_top = PAGE_H - LOGO_STRIP_H
        c.setFillColor(C_WHITE)
        c.rect(0, logo_strip_top, PAGE_W, LOGO_STRIP_H, fill=1, stroke=0)

        logo_h = 22
        logo_w = logo_h * 3.6
        logo_x = PAGE_W - MARGIN - logo_w
        logo_y = logo_strip_top + (LOGO_STRIP_H - logo_h) / 2
        if os.path.exists(LOGO_PATH):
            c.drawImage(LOGO_PATH, logo_x, logo_y,
                        width=logo_w, height=logo_h,
                        preserveAspectRatio=True, mask='auto')

        # ── Dark teal title band ────────────────────────────────────────────
        title_band_top = logo_strip_top
        title_band_btm = title_band_top - TITLE_BAND_H
        c.setFillColor(C_DARK_TEAL)
        c.rect(0, title_band_btm, PAGE_W, TITLE_BAND_H, fill=1, stroke=0)

        # Olive accent at bottom of title band
        c.setFillColor(C_OLIVE)
        c.rect(0, title_band_btm, PAGE_W, 3, fill=1, stroke=0)

        # Auto-wrap title if over 42 chars and no subtitle supplied
        if len(title) > 50 and not subtitle:
            words = title.split()
            line1, line2 = [], []
            for word in words:
                if len(' '.join(line1 + [word])) <= 42:
                    line1.append(word)
                else:
                    line2.append(word)
            subtitle = ' '.join(line2)
            title    = ' '.join(line1)

        c.setFillColor(C_WHITE)
        if subtitle:
            # Two-line layout: title + subtitle
            total_h  = SZ_TITLE + 4 + SZ_SUBTITLE
            block_y  = title_band_btm + 3 + (TITLE_BAND_H - 3 - total_h) / 2 + total_h
            c.setFont(FONT_BOLD, SZ_TITLE)
            c.drawString(MARGIN, block_y - SZ_TITLE, title)
            c.setFont(FONT_REG, SZ_SUBTITLE)
            c.setFillColor(HexColor('#6B8CBE'))   # slate blue — readable on dark navy
            c.drawString(MARGIN, block_y - SZ_TITLE - 4 - SZ_SUBTITLE, subtitle)
        else:
            title_y = title_band_btm + 3 + (TITLE_BAND_H - 3) / 2 - SZ_TITLE / 2
            c.setFont(FONT_BOLD, SZ_TITLE)
            c.drawString(MARGIN, title_y, title)

    def _draw_continuation_header(self):
        c = self.c
        c.setFillColor(C_DARK_TEAL)
        c.rect(0, PAGE_H - MINI_HEADER_H, PAGE_W, MINI_HEADER_H, fill=1, stroke=0)
        c.setFillColor(C_WHITE)
        c.setFont(FONT_REG, SZ_META)
        c.drawString(MARGIN, PAGE_H - MINI_HEADER_H + 9, self.meta.get('title', ''))
        logo_h = 14
        logo_w = logo_h * 3.6
        if os.path.exists(LOGO_WHITE_PATH):
            c.drawImage(LOGO_WHITE_PATH, PAGE_W - MARGIN - logo_w,
                        PAGE_H - MINI_HEADER_H + 6,
                        width=logo_w, height=logo_h,
                        preserveAspectRatio=True, mask='auto')

    def _draw_footer(self):
        c = self.c
        c.setStrokeColor(C_DARK_TEAL)
        c.setLineWidth(0.5)
        c.line(MARGIN, FOOTER_H, PAGE_W - MARGIN, FOOTER_H)
        c.setFillColor(C_BODY_GRAY)
        c.setFont(FONT_REG, SZ_FOOTER)
        c.drawRightString(PAGE_W - MARGIN, FOOTER_H - 14, f'Page {self.page}')

    def _draw_meta_line(self, y):
        c = self.c
        audience = self.meta.get('audience', '')
        purpose  = self.meta.get('purpose', '')
        date     = self.meta.get('date', '')
        author   = self.meta.get('author', '')
        parts    = [f'Prepared for: {audience}'] if audience else []
        if author:
            parts.append(f'By: {author}')
        if purpose:
            parts.append(purpose.capitalize())
        if date:
            parts.append(str(date))
        meta_str = '  ·  '.join(parts)
        c.setFillColor(C_BODY_GRAY)
        c.setFont(FONT_REG, SZ_META)
        c.drawString(MARGIN, y, meta_str)
        c.setStrokeColor(C_LIGHT_GRAY)
        c.setLineWidth(0.5)
        c.line(MARGIN, y - 6, PAGE_W - MARGIN, y - 6)

    # ── Space management ─────────────────────────────────────────────────────

    def new_page(self):
        self.c.showPage()
        self._start_page()

    def _floor(self):
        return FOOTER_H + MARGIN

    def ensure_space(self, needed):
        if self.y - needed < self._floor():
            self.new_page()

    # ── Content renderers ────────────────────────────────────────────────────

    def draw_lead(self, text):
        self.y -= 10
        c = self.c
        paragraphs = [p.strip() for p in re.split(r'\n\n+', text) if p.strip()]
        for para in paragraphs:
            lines = wrap_text(c, para, FONT_REG, SZ_LEAD, CONTENT_W)
            self.ensure_space(len(lines) * LH_LEAD)
            c.setFillColor(C_BODY_GRAY)
            c.setFont(FONT_REG, SZ_LEAD)
            for line in lines:
                c.drawString(MARGIN, self.y, line)
                self.y -= LH_LEAD
            self.y -= 5
        self.y -= 2

    def draw_section_header(self, text):
        self.ensure_space(LH_SECTION + LH_BODY * 2 + 24)
        self.y -= 3
        c = self.c
        # Thin olive rule
        c.setStrokeColor(C_OLIVE)
        c.setLineWidth(0.75)
        c.line(MARGIN, self.y, PAGE_W - MARGIN, self.y)
        self.y -= 14   # clear air between rule and cap-height of 12pt text
        c.setFillColor(C_DARK_TEAL)
        c.setFont(FONT_BOLD, SZ_SECTION)
        c.drawString(MARGIN, self.y, text)
        self.y -= LH_SECTION

    def draw_body(self, text):
        if not text.strip():
            return
        c = self.c
        paragraphs = [p.strip() for p in re.split(r'\n\n+', text) if p.strip()]
        for para in paragraphs:
            lines = wrap_text(c, para, FONT_REG, SZ_BODY, CONTENT_W)
            self.ensure_space(len(lines) * LH_BODY + 6)
            c.setFillColor(C_BODY_GRAY)
            c.setFont(FONT_REG, SZ_BODY)
            for line in lines:
                c.drawString(MARGIN, self.y, line)
                self.y -= LH_BODY
            self.y -= 4
        self.y -= 0

    def draw_callout(self, label, body):
        PAD  = 10
        BORD = 4   # left border width
        c    = self.c

        label_lines = wrap_text(c, label + ':', FONT_BOLD, SZ_BODY, CONTENT_W - 2 * PAD - BORD)
        body_lines  = wrap_text(c, body,         FONT_REG,  SZ_BODY, CONTENT_W - 2 * PAD - BORD)
        box_h       = 2 * PAD + (len(label_lines) + len(body_lines)) * LH_BODY + 2

        self.y -= 5
        self.ensure_space(box_h + 8)

        box_top = self.y
        box_btm = box_top - box_h

        # Background and left border
        c.setFillColor(C_LIGHT_TEAL)
        c.rect(MARGIN + BORD, box_btm, CONTENT_W - BORD, box_h, fill=1, stroke=0)
        c.setFillColor(C_DARK_TEAL)
        c.rect(MARGIN, box_btm, BORD, box_h, fill=1, stroke=0)

        y_text = box_top - PAD - SZ_BODY

        c.setFillColor(C_DARK_TEAL)
        c.setFont(FONT_BOLD, SZ_BODY)
        for line in label_lines:
            c.drawString(MARGIN + BORD + PAD, y_text, line)
            y_text -= LH_BODY

        y_text -= 2
        c.setFillColor(C_BODY_GRAY)
        c.setFont(FONT_REG, SZ_BODY)
        for line in body_lines:
            c.drawString(MARGIN + BORD + PAD, y_text, line)
            y_text -= LH_BODY

        self.y = box_btm - 10

    def draw_implication(self, text):
        PAD = 12
        c   = self.c

        hdr_lines  = wrap_text(c, 'Implication', FONT_BOLD, SZ_SECTION, CONTENT_W - 2 * PAD)
        body_lines = wrap_text(c, text,          FONT_REG,  SZ_BODY,    CONTENT_W - 2 * PAD)
        box_h = 2 * PAD + len(hdr_lines) * LH_SECTION + 6 + len(body_lines) * LH_BODY

        self.y -= 8
        self.ensure_space(box_h + 12)

        box_top = self.y
        box_btm = box_top - box_h

        c.setFillColor(C_LIGHT_TEAL)
        c.rect(MARGIN, box_btm, CONTENT_W, box_h, fill=1, stroke=0)
        # Top border rule
        c.setFillColor(C_DARK_TEAL)
        c.rect(MARGIN, box_top - 3, CONTENT_W, 3, fill=1, stroke=0)

        y_text = box_top - PAD - SZ_SECTION
        c.setFillColor(C_DARK_TEAL)
        c.setFont(FONT_BOLD, SZ_SECTION)
        for line in hdr_lines:
            c.drawString(MARGIN + PAD, y_text, line)
            y_text -= LH_SECTION

        y_text -= 6
        c.setFillColor(C_BODY_GRAY)
        c.setFont(FONT_REG, SZ_BODY)
        for line in body_lines:
            c.drawString(MARGIN + PAD, y_text, line)
            y_text -= LH_BODY

        self.y = box_btm - 8

    def draw_provenance(self):
        author  = self.meta.get('author', '')
        sources = self.meta.get('sources', []) or []
        if isinstance(sources, str):
            sources = [sources]
        lines = []
        if author:
            lines.append(f'Author: {author}')
        if sources:
            src_str = '  ·  '.join(os.path.basename(str(s)) for s in sources)
            lines.append(f'Sources: {src_str}')
        lines.append('Prepared with Claude Code  ·  /two-pager workflow')
        block_h = 10 + len(lines) * 11
        if self.y - block_h < FOOTER_H + 12:
            self.new_page()
        self.y -= 10
        self.c.setStrokeColor(C_LIGHT_GRAY)
        self.c.setLineWidth(0.5)
        self.c.line(MARGIN, self.y, PAGE_W - MARGIN, self.y)
        self.y -= 10
        self.c.setFillColor(C_BODY_GRAY)
        self.c.setFont(FONT_REG, SZ_FOOTER)
        for line in lines:
            self.c.drawString(MARGIN, self.y, line)
            self.y -= 11


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print('Usage: build_report.py <path/to/doc.md> [--out <output.pdf>]')
        sys.exit(1)

    src = sys.argv[1]
    out = None
    for i, arg in enumerate(sys.argv):
        if arg == '--out' and i + 1 < len(sys.argv):
            out = sys.argv[i + 1]

    if not os.path.exists(src):
        print(f'Error: source file not found: {src}')
        sys.exit(1)

    if out is None:
        slug = os.path.splitext(os.path.basename(src))[0]
        out  = os.path.join(PROJECT_ROOT, 'build', slug + '.pdf')

    os.makedirs(os.path.dirname(out), exist_ok=True)

    print(f'  Source : {src}')
    print(f'  Output : {out}')

    register_fonts()

    meta, blocks = parse_document(src)
    print(f'  Title  : {meta.get("title", "(untitled)")}')
    print(f'  Blocks : {len(blocks)}')

    c = canvas.Canvas(out, pagesize=letter)
    c.setTitle(meta.get('title', ''))
    c.setAuthor(meta.get('author', ''))
    c.setSubject(f"Prepared for: {meta.get('audience', '')}")

    renderer = Renderer(c, meta)

    for block in blocks:
        kind = block[0]
        if kind == 'lead':
            renderer.draw_lead(block[1])
        elif kind == 'section':
            _, header, text, callout = block
            renderer.draw_section_header(header)
            renderer.draw_body(text)
            if callout:
                renderer.draw_callout(callout[0], callout[1])
        elif kind == 'implication':
            renderer.draw_implication(block[1])

    renderer.draw_provenance()
    c.save()
    print(f'\n  Built  : {out}')
    print(f'  Pages  : {renderer.page}')

    if renderer.page > 2:
        print(f'\n  WARNING: Document is {renderer.page} pages (target: 2).')
        print('  Consider tightening the prose in the source Markdown.')
        sys.exit(2)


if __name__ == '__main__':
    main()

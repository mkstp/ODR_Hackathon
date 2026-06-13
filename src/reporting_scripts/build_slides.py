#!/usr/bin/env python3
"""build_slides.py — Generate branded PDF slide deck from a YAML content file.

Usage (run from project root):
    python3 src/scripts/build_slides.py docs/my_deck.yaml
    python3 src/scripts/build_slides.py docs/my_deck.yaml --out build/my_deck.pdf

Layouts:
    cover          Full-bleed image top 62%, dark teal panel below
    closing        Mirror of cover; thank-you / closing page
    agenda         Numbered section list on white background
    section        Full dark teal divider with portrait image left
    content        Progress bar + subhead + title + bullets
    content-image  content layout with right-panel image or chart
    chart          Full-width chart or table below title (no body text)
    two-column     Two labeled panels (light gray / dark teal) side by side
    quote          Full dark teal; centered pull-quote
    stat           White; oversized metric number + label + context
    about          Org info: teal header, about text left, address + offices right

508 compliance notes:
    All text colors validated >= WCAG AA. Minimum body 16pt, footer 11pt.
    Amber (#E8863A) used for decoration only — never as text on any background.
    Slate blue (#6B8CBE) restricted to display text >= 18pt regular / >= 14pt bold.
    Progress bar uses color + "Section X of N" text (not color-only signalling).
    Run src/scripts/check_508.py to validate the design system.
"""

import os
import sys
import yaml
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfgen import canvas

try:
    from chart_utils import render_chart as _render_chart
    _CHARTS_AVAILABLE = True
except ImportError:
    _CHARTS_AVAILABLE = False

# ── Page dimensions ───────────────────────────────────────────────────────────
PAGE_W, PAGE_H = landscape(letter)   # 792 × 612 pt
MARGIN         = 48
MARGIN_R       = 40
FOOTER_H       = 36
PROGRESS_H     = 8
CONTENT_TOP    = PAGE_H - PROGRESS_H - 76   # 528 pt
CONTENT_BTM    = FOOTER_H + 16              # 52 pt

# ── Brand colors (508-validated) ──────────────────────────────────────────────
# Navy       #2E4057 — 10.57:1 on white — all sizes
# Body Gray  #595959 — 7.00:1 on white  — all sizes
# Slate Blue #6B8CBE — 3.43:1 on white  — large text only (>=18pt / >=14pt bold)
# Amber      #E8863A — 2.66:1 on white  — DECORATION ONLY, never text on white
C_DARK_TEAL  = HexColor('#2E4057')
C_STEEL_BLUE = HexColor('#6B8CBE')
C_OLIVE      = HexColor('#E8863A')
C_BODY_GRAY  = HexColor('#595959')
C_LIGHT_GRAY = HexColor('#EFEFEF')
C_WHITE      = HexColor('#FFFFFF')

# ── Type scale (508-compliant) ────────────────────────────────────────────────
SZ_COVER_TITLE   = 30   # bold   large text
SZ_SECTION_TITLE = 34   # regular large text
SZ_SLIDE_TITLE   = 22   # bold   large text (>=14pt bold)
SZ_SUBHEAD       = 14   # bold   large text (>=14pt bold); dark teal only
SZ_BODY          = 16   # regular; use dark teal or body gray only
SZ_AGENDA_ITEM   = 18   # regular large text
SZ_STAT_NUMBER   = 64   # bold   display
SZ_STAT_LABEL    = 22   # bold   large text
SZ_QUOTE         = 20   # regular large text
SZ_ATTRIBUTION   = 14   # bold   large text
SZ_FOOTER        = 11   # regular; minimum defensible
SZ_PROGRESS      = 11   # regular; "Section X of N" indicator

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_REG  = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LOGO_PATH       = os.path.join(PROJECT_ROOT, 'assets', 'images', 'logo.png')
LOGO_WHITE_PATH = os.path.join(PROJECT_ROOT, 'assets', 'images', 'logo_white.png')


def register_fonts():
    global FONT_REG, FONT_BOLD
    print('  Font: Helvetica')


# ── Text utilities ────────────────────────────────────────────────────────────
def wrap_text(c, text, font, size, max_width):
    words = str(text).split()
    if not words:
        return ['']
    lines, line, line_w = [], [], 0
    for word in words:
        w = c.stringWidth(word + ' ', font, size)
        if line and line_w + w > max_width:
            lines.append(' '.join(line))
            line, line_w = [word], w
        else:
            line.append(word)
            line_w += w
    if line:
        lines.append(' '.join(line))
    return lines


def draw_body(c, items, x, top_y, max_w, btm_y=None, text_color=None):
    """Render a bulleted list. Returns the y-coordinate after the last item."""
    if btm_y is None:
        btm_y = CONTENT_BTM
    text_color = text_color or C_BODY_GRAY
    y = top_y
    for item in items:
        if isinstance(item, str):
            text, level = item, 1
        else:
            text  = str(item.get('text', ''))
            level = int(item.get('level', 1))

        font_size = SZ_BODY if level == 1 else SZ_BODY - 2
        line_h    = font_size + 7
        indent    = x + (0 if level == 1 else 20)
        item_w    = max_w - (indent - x) - 8

        lines = wrap_text(c, text, FONT_REG, font_size, item_w)
        for i, line in enumerate(lines):
            if y < btm_y:
                return y
            c.setFont(FONT_REG, font_size)
            c.setFillColor(text_color)
            if i == 0:
                c.drawString(indent - 14, y, '–')
            c.drawString(indent, y, line)
            y -= line_h
        y -= 6
    return y


# ── Decorative elements ───────────────────────────────────────────────────────
def draw_venn(c, cx, cy, r=34, alpha=0.15):
    """Ghost Venn circles — decorative only, carries no information."""
    offset = r * 0.58
    circles = [
        (cx,                cy + offset * 0.55, HexColor('#E8863A')),
        (cx - offset * 0.6, cy - offset * 0.4,  HexColor('#7A7A7A')),
        (cx + offset * 0.6, cy - offset * 0.4,  HexColor('#6BBCD4')),
    ]
    for vx, vy, col in circles:
        c.setFillColor(Color(col.red, col.green, col.blue, alpha=alpha))
        c.circle(vx, vy, r, fill=1, stroke=0)


def draw_image_zone(c, path, x, y, w, h, alt_text='', fit='fill'):
    """Draw an image into the zone. fit='fill' crops to fill; fit='contain' letterboxes."""
    if path:
        abs_path = path if os.path.isabs(path) else os.path.join(PROJECT_ROOT, path)
        if os.path.exists(abs_path):
            try:
                from reportlab.lib.utils import ImageReader
                img    = ImageReader(abs_path)
                iw, ih = img.getSize()
                if fit == 'contain':
                    scale  = min(w / iw, h / ih)
                    sw, sh = iw * scale, ih * scale
                    ox     = x + (w - sw) / 2
                    oy     = y + (h - sh) / 2
                    c.drawImage(abs_path, ox, oy, width=sw, height=sh, mask='auto')
                else:
                    scale  = max(w / iw, h / ih)
                    sw, sh = iw * scale, ih * scale
                    dx     = (sw - w) / 2
                    dy     = (sh - h) / 2
                    c.saveState()
                    p = c.beginPath()
                    p.rect(x, y, w, h)
                    c.clipPath(p, stroke=0, fill=0)
                    c.drawImage(abs_path, x - dx, y - dy, width=sw, height=sh, mask='auto')
                    c.restoreState()
                return
            except Exception:
                pass

    # Placeholder — dark teal fill with alt text
    c.setFillColor(C_DARK_TEAL)
    c.rect(x, y, w, h, fill=1, stroke=0)
    if alt_text:
        c.saveState()
        p = c.beginPath()
        p.rect(x, y, w, h)
        c.clipPath(p, stroke=0, fill=0)
        c.setFillColor(Color(1, 1, 1, alpha=0.55))
        c.setFont(FONT_REG, SZ_FOOTER)
        label   = f'[Image: {alt_text}]'
        llines  = wrap_text(c, label, FONT_REG, SZ_FOOTER, w - 20)
        ty      = y + h / 2 + len(llines) * 8
        for ll in llines:
            c.drawCentredString(x + w / 2, ty, ll)
            ty -= 16
        c.restoreState()


# ── Progress bar ──────────────────────────────────────────────────────────────
def draw_progress_bar(c, sec_idx, total, sec_name):
    """Colored segments + "Section X of N: Name" text (not color-only — 508 req)."""
    seg_w = PAGE_W / total
    for i in range(total):
        color = C_DARK_TEAL if i == sec_idx else (C_STEEL_BLUE if i < sec_idx else C_LIGHT_GRAY)
        c.setFillColor(color)
        c.rect(i * seg_w, PAGE_H - PROGRESS_H, seg_w, PROGRESS_H, fill=1, stroke=0)

    c.setFont(FONT_REG, SZ_PROGRESS)
    c.setFillColor(C_BODY_GRAY)
    label = f'Section {sec_idx + 1} of {total}: {sec_name}'
    c.drawRightString(PAGE_W - MARGIN_R, PAGE_H - PROGRESS_H - 14, label)


# ── Footer helpers ────────────────────────────────────────────────────────────
def draw_footer(c, page_num, presentation_title=''):
    """Standard footer for white-background slides."""
    c.setStrokeColor(C_LIGHT_GRAY)
    c.setLineWidth(0.5)
    c.line(MARGIN, FOOTER_H, PAGE_W - MARGIN_R, FOOTER_H)

    if presentation_title:
        c.setFont(FONT_REG, SZ_FOOTER)
        c.setFillColor(C_BODY_GRAY)
        c.drawString(MARGIN, 14, presentation_title)

    # Dash above page number
    num_str = str(page_num)
    right_x = PAGE_W - MARGIN_R
    num_w   = c.stringWidth(num_str, FONT_REG, SZ_FOOTER)
    dash_cx = right_x - num_w / 2
    c.setStrokeColor(C_BODY_GRAY)
    c.setLineWidth(1)
    c.line(dash_cx - 9, 27, dash_cx + 9, 27)
    c.setFont(FONT_REG, SZ_FOOTER)
    c.setFillColor(C_BODY_GRAY)
    c.drawRightString(right_x, 14, num_str)


def draw_dark_footer(c, page_num):
    """Minimal page number for dark-background slides."""
    num_str = str(page_num)
    right_x = PAGE_W - MARGIN_R
    num_w   = c.stringWidth(num_str, FONT_REG, SZ_FOOTER)
    dash_cx = right_x - num_w / 2
    c.setStrokeColor(Color(1, 1, 1, alpha=0.5))
    c.setLineWidth(1)
    c.line(dash_cx - 9, 27, dash_cx + 9, 27)
    c.setFont(FONT_REG, SZ_FOOTER)
    c.setFillColor(Color(1, 1, 1, alpha=0.7))
    c.drawRightString(right_x, 14, num_str)


# ── Layout renderers ──────────────────────────────────────────────────────────

def render_cover(c, slide, page_num, ctx):
    PANEL_H  = int(PAGE_H * 0.38)
    IMG_H    = PAGE_H - PANEL_H
    PIPE_X   = MARGIN + 118
    PIPE_GAP = 20

    draw_image_zone(c, slide.get('image', ''), 0, PANEL_H, PAGE_W, IMG_H,
                    alt_text=slide.get('image_alt', 'Cover image'))

    c.setFillColor(C_DARK_TEAL)
    c.rect(0, 0, PAGE_W, PANEL_H, fill=1, stroke=0)

    draw_venn(c, PAGE_W - 56, PANEL_H * 0.7, r=32, alpha=0.12)

    if os.path.exists(LOGO_WHITE_PATH):
        lh, lw = 40, 108
        c.drawImage(LOGO_WHITE_PATH, MARGIN - 5, 14,
                    width=lw, height=lh, preserveAspectRatio=True, mask='auto')

    c.setStrokeColor(Color(1, 1, 1, alpha=0.35))
    c.setLineWidth(1)
    c.line(PIPE_X, 18, PIPE_X, PANEL_H - 18)

    tx = PIPE_X + PIPE_GAP
    max_tw = PAGE_W - tx - MARGIN_R
    ty = PANEL_H - 48

    title = slide.get('title', '')
    for line in wrap_text(c, title, FONT_BOLD, SZ_COVER_TITLE, max_tw):
        c.setFont(FONT_BOLD, SZ_COVER_TITLE)
        c.setFillColor(C_WHITE)
        c.drawString(tx, ty, line)
        ty -= SZ_COVER_TITLE + 6

    subtitle = slide.get('subtitle', '')
    if subtitle:
        ty -= 4
        c.setFont(FONT_REG, SZ_BODY)
        c.setFillColor(Color(1, 1, 1, alpha=0.80))
        c.drawString(tx, ty, subtitle)

    meta = slide.get('meta', '')
    if meta:
        c.setFont(FONT_REG, SZ_FOOTER)
        c.setFillColor(Color(1, 1, 1, alpha=0.58))
        c.drawString(tx, 14, meta)


def render_closing(c, slide, page_num, ctx):
    PANEL_H  = int(PAGE_H * 0.38)
    IMG_H    = PAGE_H - PANEL_H
    PIPE_X   = MARGIN + 118
    PIPE_GAP = 20

    draw_image_zone(c, slide.get('image', ''), 0, PANEL_H, PAGE_W, IMG_H,
                    alt_text=slide.get('image_alt', 'Closing image'))

    c.setFillColor(C_DARK_TEAL)
    c.rect(0, 0, PAGE_W, PANEL_H, fill=1, stroke=0)

    draw_venn(c, PAGE_W - 56, PANEL_H * 0.7, r=32, alpha=0.12)

    if os.path.exists(LOGO_WHITE_PATH):
        lh, lw = 40, 108
        c.drawImage(LOGO_WHITE_PATH, MARGIN - 5, 14,
                    width=lw, height=lh, preserveAspectRatio=True, mask='auto')

    c.setStrokeColor(Color(1, 1, 1, alpha=0.35))
    c.setLineWidth(1)
    c.line(PIPE_X, 18, PIPE_X, PANEL_H - 18)

    tx = PIPE_X + PIPE_GAP
    max_tw = PAGE_W - tx - MARGIN_R
    ty = PANEL_H - 48

    title = slide.get('title', 'Thank You')
    for line in wrap_text(c, title, FONT_BOLD, SZ_COVER_TITLE, max_tw):
        c.setFont(FONT_BOLD, SZ_COVER_TITLE)
        c.setFillColor(C_WHITE)
        c.drawString(tx, ty, line)
        ty -= SZ_COVER_TITLE + 6

    contact = slide.get('contact', '')
    if contact:
        ty -= 4
        c.setFont(FONT_REG, SZ_BODY)
        c.setFillColor(Color(1, 1, 1, alpha=0.80))
        c.drawString(tx, ty, contact)

    website = slide.get('website', '')
    if website:
        c.setFont(FONT_REG, SZ_FOOTER)
        c.setFillColor(Color(1, 1, 1, alpha=0.58))
        c.drawString(tx, 14, website)


def render_section(c, slide, page_num, ctx):
    IMG_W  = int(PAGE_W * 0.22)
    PIPE_X = IMG_W + 14
    TEXT_X = PIPE_X + 22

    c.setFillColor(C_DARK_TEAL)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    draw_venn(c, PAGE_W * 0.88, PAGE_H * 0.22, r=96, alpha=0.09)

    # White base prevents teal bleed-through; overlay then controls the tint explicitly
    c.setFillColor(C_WHITE)
    c.rect(0, 0, IMG_W, PAGE_H, fill=1, stroke=0)
    draw_image_zone(c, slide.get('image', ''), 0, 0, IMG_W, PAGE_H,
                    alt_text=slide.get('image_alt', 'Section image'))
    c.setFillColor(Color(C_DARK_TEAL.red, C_DARK_TEAL.green, C_DARK_TEAL.blue, alpha=0.42))
    c.rect(0, 0, IMG_W, PAGE_H, fill=1, stroke=0)

    c.setStrokeColor(Color(1, 1, 1, alpha=0.45))
    c.setLineWidth(1)
    c.line(PIPE_X, 72, PIPE_X, PAGE_H - 72)

    max_tw = PAGE_W - TEXT_X - MARGIN_R
    ty     = PAGE_H * 0.63

    subhead = slide.get('subhead', '')
    if subhead:
        c.setFont(FONT_BOLD, SZ_SUBHEAD)
        c.setFillColor(Color(1, 1, 1, alpha=0.72))
        c.drawString(TEXT_X, ty, subhead.upper())
        ty -= SZ_SUBHEAD + 26

    title = slide.get('title', '')
    c.setFillColor(C_WHITE)
    for line in wrap_text(c, title, FONT_REG, SZ_SECTION_TITLE, max_tw):
        c.setFont(FONT_REG, SZ_SECTION_TITLE)
        c.drawString(TEXT_X, ty, line)
        ty -= SZ_SECTION_TITLE + 8

    draw_dark_footer(c, page_num)


def render_agenda(c, slide, page_num, ctx):
    c.setFillColor(C_WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Thin teal accent strip at top
    c.setFillColor(C_DARK_TEAL)
    c.rect(0, PAGE_H - 10, PAGE_W, 10, fill=1, stroke=0)

    c.setFont(FONT_BOLD, SZ_SLIDE_TITLE)
    c.setFillColor(C_DARK_TEAL)
    c.drawString(MARGIN, PAGE_H - 76, slide.get('title', 'Agenda'))

    c.setStrokeColor(C_LIGHT_GRAY)
    c.setLineWidth(0.5)
    c.line(MARGIN, PAGE_H - 90, PAGE_W - MARGIN_R, PAGE_H - 90)

    items = slide.get('items', [])
    n     = len(items)
    if not items:
        draw_footer(c, page_num, ctx.get('title', ''))
        return

    body_top  = PAGE_H - 108
    body_btm  = FOOTER_H + 20
    available = body_top - body_btm
    item_h    = min(available / n, 54)
    circle_r  = 14
    colors    = [C_DARK_TEAL, C_STEEL_BLUE] * 8

    for i, item in enumerate(items):
        label = item if isinstance(item, str) else str(item.get('label', ''))
        cy = body_top - i * item_h - item_h / 2

        c.setFillColor(colors[i % 2])
        c.circle(MARGIN + circle_r, cy, circle_r, fill=1, stroke=0)
        c.setFont(FONT_BOLD, SZ_SUBHEAD)
        c.setFillColor(C_WHITE)
        nw = c.stringWidth(str(i + 1), FONT_BOLD, SZ_SUBHEAD)
        c.drawString(MARGIN + circle_r - nw / 2, cy - 5, str(i + 1))

        c.setFont(FONT_REG, SZ_AGENDA_ITEM)
        c.setFillColor(C_BODY_GRAY)
        c.drawString(MARGIN + circle_r * 2 + 16, cy - 6, label)

    draw_footer(c, page_num, ctx.get('title', ''))


def _resolve_section(slide, ctx):
    """Return (sec_idx, total) or (-1, 0) if not trackable."""
    sections = ctx.get('sections', [])
    sec_name = slide.get('section', '')
    if not sections or sec_name not in sections:
        return -1, 0, sec_name
    return sections.index(sec_name), len(sections), sec_name


def render_content(c, slide, page_num, ctx):
    c.setFillColor(C_WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    sec_idx, total, sec_name = _resolve_section(slide, ctx)
    if sec_idx >= 0:
        draw_progress_bar(c, sec_idx, total, sec_name)

    ty = CONTENT_TOP
    subhead = slide.get('subhead', '')
    if subhead:
        c.setFont(FONT_BOLD, SZ_SUBHEAD)
        c.setFillColor(C_DARK_TEAL)
        c.drawString(MARGIN, ty, subhead.upper())
        ty -= SZ_SUBHEAD + 20

    title = slide.get('title', '')
    if title:
        max_tw = PAGE_W - MARGIN - MARGIN_R
        for line in wrap_text(c, title, FONT_BOLD, SZ_SLIDE_TITLE, max_tw):
            c.setFont(FONT_BOLD, SZ_SLIDE_TITLE)
            c.setFillColor(C_DARK_TEAL)
            c.drawString(MARGIN, ty, line)
            ty -= SZ_SLIDE_TITLE + 4
        ty -= 8

    c.setStrokeColor(C_LIGHT_GRAY)
    c.setLineWidth(0.5)
    c.line(MARGIN, ty, PAGE_W - MARGIN_R, ty)
    ty -= 20

    body = slide.get('body', [])
    if body:
        draw_body(c, body, MARGIN, ty, PAGE_W - MARGIN - MARGIN_R)

    draw_footer(c, page_num, ctx.get('title', ''))


def render_content_image(c, slide, page_num, ctx):
    c.setFillColor(C_WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    sec_idx, total, sec_name = _resolve_section(slide, ctx)
    if sec_idx >= 0:
        draw_progress_bar(c, sec_idx, total, sec_name)

    TEXT_W = int(PAGE_W * 0.53)
    IMG_X  = TEXT_W + 12
    IMG_W  = PAGE_W - IMG_X
    IMG_Y  = FOOTER_H
    IMG_H  = CONTENT_TOP - FOOTER_H + 12

    chart_spec = slide.get('chart')
    if chart_spec and _CHARTS_AVAILABLE:
        reader = _render_chart(chart_spec, width_pt=IMG_W, height_pt=IMG_H)
        c.drawImage(reader, IMG_X, IMG_Y, width=IMG_W, height=IMG_H, mask='auto')
    elif chart_spec:
        print('  Warning: chart key found but matplotlib is not installed — rendering placeholder')
        draw_image_zone(c, '', IMG_X, IMG_Y, IMG_W, IMG_H, alt_text='Chart (matplotlib not installed)')
    else:
        draw_image_zone(c, slide.get('image', ''), IMG_X, IMG_Y, IMG_W, IMG_H,
                        alt_text=slide.get('image_alt', ''),
                        fit=slide.get('image_fit', 'fill'))

    caption = slide.get('caption', '')
    if caption:
        cap_h = 22
        c.setFillColor(Color(C_DARK_TEAL.red, C_DARK_TEAL.green, C_DARK_TEAL.blue, alpha=0.88))
        c.rect(IMG_X, IMG_Y, IMG_W, cap_h, fill=1, stroke=0)
        c.setFont(FONT_REG, SZ_FOOTER)
        c.setFillColor(C_WHITE)
        c.drawString(IMG_X + 10, IMG_Y + 7, caption)

    ty = CONTENT_TOP
    subhead = slide.get('subhead', '')
    if subhead:
        c.setFont(FONT_BOLD, SZ_SUBHEAD)
        c.setFillColor(C_DARK_TEAL)
        c.drawString(MARGIN, ty, subhead.upper())
        ty -= SZ_SUBHEAD + 20

    title = slide.get('title', '')
    if title:
        for line in wrap_text(c, title, FONT_BOLD, SZ_SLIDE_TITLE, TEXT_W - MARGIN - 8):
            c.setFont(FONT_BOLD, SZ_SLIDE_TITLE)
            c.setFillColor(C_DARK_TEAL)
            c.drawString(MARGIN, ty, line)
            ty -= SZ_SLIDE_TITLE + 4
        ty -= 8

    c.setStrokeColor(C_LIGHT_GRAY)
    c.setLineWidth(0.5)
    c.line(MARGIN, ty, TEXT_W - 8, ty)
    ty -= 20

    body = slide.get('body', [])
    if body:
        draw_body(c, body, MARGIN, ty, TEXT_W - MARGIN - 8)

    draw_footer(c, page_num, ctx.get('title', ''))


def render_two_column(c, slide, page_num, ctx):
    c.setFillColor(C_WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    sec_idx, total, sec_name = _resolve_section(slide, ctx)
    if sec_idx >= 0:
        draw_progress_bar(c, sec_idx, total, sec_name)

    ty = CONTENT_TOP
    title = slide.get('title', '')
    if title:
        c.setFont(FONT_BOLD, SZ_SLIDE_TITLE)
        c.setFillColor(C_DARK_TEAL)
        c.drawString(MARGIN, ty, title)
        ty -= SZ_SLIDE_TITLE + 10

    c.setStrokeColor(C_LIGHT_GRAY)
    c.setLineWidth(0.5)
    c.line(MARGIN, ty, PAGE_W - MARGIN_R, ty)
    ty -= 14

    COL_GAP   = 16
    COL_W     = (PAGE_W - MARGIN - MARGIN_R - COL_GAP) / 2
    left_x    = MARGIN
    right_x   = MARGIN + COL_W + COL_GAP
    panel_btm = FOOTER_H + 8
    panel_h   = ty - panel_btm

    left  = slide.get('left',  {})
    right = slide.get('right', {})

    c.setFillColor(C_LIGHT_GRAY)
    c.roundRect(left_x, panel_btm, COL_W, panel_h, 4, fill=1, stroke=0)
    c.setFillColor(C_DARK_TEAL)
    c.roundRect(right_x, panel_btm, COL_W, panel_h, 4, fill=1, stroke=0)

    label_y = ty - 28
    left_label = left.get('label', '')
    if left_label:
        c.setFont(FONT_BOLD, SZ_SUBHEAD)
        c.setFillColor(C_DARK_TEAL)
        c.drawString(left_x + 14, label_y, left_label.upper())

    right_label = right.get('label', '')
    if right_label:
        c.setFont(FONT_BOLD, SZ_SUBHEAD)
        c.setFillColor(C_WHITE)
        c.drawString(right_x + 14, label_y, right_label.upper())

    body_top = label_y - 22
    draw_body(c, left.get('body', []),  left_x + 14,  body_top, COL_W - 28, panel_btm + 8, C_BODY_GRAY)
    draw_body(c, right.get('body', []), right_x + 14, body_top, COL_W - 28, panel_btm + 8, C_WHITE)

    draw_footer(c, page_num, ctx.get('title', ''))


def render_quote(c, slide, page_num, ctx):
    c.setFillColor(C_DARK_TEAL)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    draw_venn(c, PAGE_W * 0.88, PAGE_H * 0.22, r=96, alpha=0.09)

    # Large decorative open-quote glyph — purely decorative, no information
    c.setFont(FONT_BOLD, 80)
    c.setFillColor(Color(1, 1, 1, alpha=0.18))
    c.drawString(MARGIN - 4, PAGE_H * 0.76, '”')

    quote  = slide.get('quote', '')
    max_qw = PAGE_W * 0.68
    q_x    = MARGIN + 28
    qlines = wrap_text(c, quote, FONT_REG, SZ_QUOTE, max_qw)
    total_h = len(qlines) * (SZ_QUOTE + 10)
    ty = PAGE_H / 2 + total_h / 2 + 20

    c.setFillColor(C_WHITE)
    for line in qlines:
        c.setFont(FONT_REG, SZ_QUOTE)
        c.drawString(q_x, ty, line)
        ty -= SZ_QUOTE + 10

    attribution = slide.get('attribution', '')
    if attribution:
        ty -= 14
        c.setFont(FONT_BOLD, SZ_ATTRIBUTION)
        c.setFillColor(Color(1, 1, 1, alpha=0.72))
        c.drawString(q_x, ty, f'—  {attribution}')

    draw_dark_footer(c, page_num)


def render_stat(c, slide, page_num, ctx):
    c.setFillColor(C_WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    sec_idx, total, sec_name = _resolve_section(slide, ctx)
    if sec_idx >= 0:
        draw_progress_bar(c, sec_idx, total, sec_name)

    # Thin olive decorative rule — geometric accent, carries no information
    c.setStrokeColor(C_OLIVE)
    c.setLineWidth(3)
    rule_y = PAGE_H * 0.62
    c.line(MARGIN, rule_y, MARGIN + 56, rule_y)

    cy = PAGE_H * 0.50

    stat_number = str(slide.get('stat', ''))
    c.setFont(FONT_BOLD, SZ_STAT_NUMBER)
    c.setFillColor(C_DARK_TEAL)
    c.drawCentredString(PAGE_W / 2, cy, stat_number)

    label = slide.get('label', '')
    if label:
        c.setFont(FONT_BOLD, SZ_STAT_LABEL)
        c.setFillColor(C_DARK_TEAL)
        c.drawCentredString(PAGE_W / 2, cy - SZ_STAT_NUMBER - 14, label)

    context = slide.get('context', '')
    if context:
        ctx_y = cy - SZ_STAT_NUMBER - SZ_STAT_LABEL - 30
        c.setFont(FONT_REG, SZ_BODY)
        c.setFillColor(C_BODY_GRAY)
        for line in wrap_text(c, context, FONT_REG, SZ_BODY, PAGE_W * 0.60):
            c.drawCentredString(PAGE_W / 2, ctx_y, line)
            ctx_y -= SZ_BODY + 6

    draw_footer(c, page_num, ctx.get('title', ''))


def render_about(c, slide, page_num, ctx):
    HEADER_H = int(PAGE_H * 0.28)
    COL_SPLIT = PAGE_W * 0.54
    RIGHT_X   = COL_SPLIT + 16
    RIGHT_W   = PAGE_W - RIGHT_X - MARGIN_R
    LEFT_W    = COL_SPLIT - MARGIN - 16

    c.setFillColor(C_WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    c.setFillColor(C_DARK_TEAL)
    c.rect(0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, fill=1, stroke=0)

    draw_venn(c, PAGE_W * 0.88, PAGE_H - HEADER_H / 2, r=44, alpha=0.15)

    ty = PAGE_H - HEADER_H - 36

    # Left column — about text
    about_title = slide.get('about_title', 'About Us')
    c.setFont(FONT_BOLD, SZ_SLIDE_TITLE)
    c.setFillColor(C_STEEL_BLUE)
    c.drawString(MARGIN, ty, about_title)
    ty -= SZ_SLIDE_TITLE + 16

    for para in slide.get('about_body', []):
        for line in wrap_text(c, para, FONT_REG, SZ_BODY - 1, LEFT_W):
            c.setFont(FONT_REG, SZ_BODY - 1)
            c.setFillColor(C_BODY_GRAY)
            c.drawString(MARGIN, ty, line)
            ty -= SZ_BODY + 3
        ty -= 10

    website = slide.get('website', '')
    if website:
        ty -= 4
        label = 'FOR MORE INFORMATION:'
        lw = c.stringWidth(label + ' ', FONT_BOLD, SZ_BODY - 1)
        c.setFont(FONT_BOLD, SZ_BODY - 1)
        c.setFillColor(C_BODY_GRAY)
        c.drawString(MARGIN, ty, label)
        c.setFillColor(C_STEEL_BLUE)
        c.drawString(MARGIN + lw, ty, website)

    # Right column — steel blue rule, address, offices
    ty_r = PAGE_H - HEADER_H - 28
    c.setFillColor(C_STEEL_BLUE)
    c.rect(RIGHT_X, ty_r, RIGHT_W, 7, fill=1, stroke=0)
    ty_r -= 7 + 18

    for line in slide.get('address', []):
        c.setFont(FONT_REG, SZ_BODY - 1)
        c.setFillColor(C_BODY_GRAY)
        c.drawString(RIGHT_X, ty_r, line)
        ty_r -= SZ_BODY + 3
    ty_r -= 14

    for office in slide.get('offices', []):
        c.setFont(FONT_BOLD, SZ_SUBHEAD)
        c.setFillColor(C_DARK_TEAL)
        c.drawString(RIGHT_X, ty_r, office)
        ty_r -= SZ_SUBHEAD + 8

    if os.path.exists(LOGO_PATH):
        c.drawImage(LOGO_PATH, MARGIN - 5, 14, width=108, height=40,
                    preserveAspectRatio=True, mask='auto')


# ── Chart slide ───────────────────────────────────────────────────────────────
def render_chart_slide(c, slide, page_num, ctx):
    """Full-width chart or table below subhead + title. No body text column."""
    c.setFillColor(C_WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    sec_idx, total, sec_name = _resolve_section(slide, ctx)
    if sec_idx >= 0:
        draw_progress_bar(c, sec_idx, total, sec_name)

    ty = CONTENT_TOP
    subhead = slide.get('subhead', '')
    if subhead:
        c.setFont(FONT_BOLD, SZ_SUBHEAD)
        c.setFillColor(C_DARK_TEAL)
        c.drawString(MARGIN, ty, subhead.upper())
        ty -= SZ_SUBHEAD + 20

    title = slide.get('title', '')
    full_w = PAGE_W - MARGIN - MARGIN_R
    if title:
        for line in wrap_text(c, title, FONT_BOLD, SZ_SLIDE_TITLE, full_w):
            c.setFont(FONT_BOLD, SZ_SLIDE_TITLE)
            c.setFillColor(C_DARK_TEAL)
            c.drawString(MARGIN, ty, line)
            ty -= SZ_SLIDE_TITLE + 4
        ty -= 8

    c.setStrokeColor(C_LIGHT_GRAY)
    c.setLineWidth(0.5)
    c.line(MARGIN, ty, PAGE_W - MARGIN_R, ty)
    ty -= 12

    chart_h = ty - CONTENT_BTM
    chart_spec = slide.get('chart', {})
    if chart_spec and _CHARTS_AVAILABLE:
        reader = _render_chart(chart_spec, width_pt=full_w, height_pt=chart_h)
        c.drawImage(reader, MARGIN, CONTENT_BTM, width=full_w, height=chart_h, mask='auto')
    elif chart_spec:
        print('  Warning: chart key found but matplotlib is not installed — rendering placeholder')
        draw_image_zone(c, '', MARGIN, CONTENT_BTM, full_w, chart_h, alt_text='Chart (matplotlib not installed)')
    else:
        draw_image_zone(c, slide.get('image', ''), MARGIN, CONTENT_BTM, full_w, chart_h,
                        alt_text=slide.get('image_alt', ''))

    draw_footer(c, page_num, ctx.get('title', ''))


def render_full_image(c, slide, page_num, ctx):
    """Full-slide image. Optional title renders as a semi-transparent caption bar at the bottom."""
    c.setFillColor(C_WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    title = slide.get('title', '')
    cap_h = 38 if title else 0

    draw_image_zone(c, slide.get('image', ''), 0, cap_h, PAGE_W, PAGE_H - cap_h,
                    alt_text=slide.get('image_alt', ''),
                    fit=slide.get('image_fit', 'contain'))

    if title:
        c.setFillColor(Color(C_DARK_TEAL.red, C_DARK_TEAL.green, C_DARK_TEAL.blue, alpha=0.88))
        c.rect(0, 0, PAGE_W, cap_h, fill=1, stroke=0)
        c.setFont(FONT_BOLD, SZ_SUBHEAD)
        c.setFillColor(C_WHITE)
        c.drawCentredString(PAGE_W / 2, 13, title)

    draw_dark_footer(c, page_num)


# ── Dispatcher ────────────────────────────────────────────────────────────────
RENDERERS = {
    'cover':         render_cover,
    'closing':       render_closing,
    'section':       render_section,
    'agenda':        render_agenda,
    'content':       render_content,
    'content-image': render_content_image,
    'chart':         render_chart_slide,
    'two-column':    render_two_column,
    'quote':         render_quote,
    'stat':          render_stat,
    'about':         render_about,
    'full-image':    render_full_image,
}


# ── Builder ───────────────────────────────────────────────────────────────────
def build(input_path, output_path):
    with open(input_path) as f:
        deck = yaml.safe_load(f)

    slides   = deck.get('slides', [])
    sections = deck.get('sections', [])
    ctx      = {'title': deck.get('title', ''), 'sections': sections}

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    cv = canvas.Canvas(output_path, pagesize=landscape(letter))
    for i, slide in enumerate(slides, start=1):
        layout   = slide.get('layout', 'content')
        renderer = RENDERERS.get(layout, render_content)
        renderer(cv, slide, i, ctx)
        cv.showPage()

    cv.save()
    print(f'  Built {len(slides)} slides -> {output_path}')


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)

    input_file  = args[0]
    output_file = args[2] if len(args) > 2 and args[1] == '--out' else None
    if output_file is None:
        base        = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(PROJECT_ROOT, 'build', base + '.pdf')

    if not os.path.exists(input_file):
        print(f'Error: file not found: {input_file}')
        sys.exit(1)

    print(f'Building: {input_file}')
    register_fonts()
    build(input_file, output_file)

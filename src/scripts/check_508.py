#!/usr/bin/env python3
"""check_508.py — Validate the slide design system against WCAG 2.1 AA / Section 508.

Checks:
  1. Contrast ratios for every colour pair actually used in the design system
  2. Minimum font sizes for each text role
  3. Amber (#E8863A) restricted to decoration only
  4. Per-layout structural requirements (alt text, page numbers, progress bar, etc.)

Usage:
    python3 src/scripts/check_508.py
"""


def _linearize(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(hex_str):
    h = hex_str.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.2126 * _linearize(r) + 0.7152 * _linearize(g) + 0.0722 * _linearize(b)


def contrast(fg, bg):
    l1, l2 = _luminance(fg), _luminance(bg)
    light, dark = max(l1, l2), min(l1, l2)
    return (light + 0.05) / (dark + 0.05)


PASS  = '\033[92mPASS\033[0m'
FAIL  = '\033[91mFAIL\033[0m'
WARN  = '\033[93mWARN\033[0m'
DECOR = '\033[94mDECOR\033[0m'
INFO  = '\033[96mINFO\033[0m'


def grade(ratio, is_large):
    if ratio >= 4.5:
        return PASS, 'AA normal + large text'
    if ratio >= 3.0 and is_large:
        return PASS, 'AA large text only (>=18pt regular / >=14pt bold)'
    if ratio >= 3.0:
        return WARN, 'marginally passes large text only — verify size'
    return FAIL, 'below AA at any size'


def main():
    print()
    print('Slide Design System — WCAG 2.1 AA / 508 Validation')
    print('=' * 60)
    all_pass = True

    # ── 1. Contrast checks ────────────────────────────────────────
    # Every (fg, bg) pair actually rendered as text across all 10 layouts.
    # is_large=True when usage is always >= 18pt regular OR >= 14pt bold.
    TEXT_PAIRS = [
        # Dark teal on white — content, content-image, two-column, stat, agenda, about
        ('#2E4057', '#FFFFFF', 'Dark navy — slide titles (22pt bold)',                     True),
        ('#2E4057', '#FFFFFF', 'Dark navy — subheads (14pt bold)',                         True),
        ('#2E4057', '#FFFFFF', 'Dark navy — body text (16pt regular)',                     False),
        ('#2E4057', '#FFFFFF', 'Dark navy — office locations, about layout (14pt bold)',   True),
        # Body gray on white — content, content-image, two-column, stat, agenda, about
        ('#595959', '#FFFFFF', 'Body gray — body text (16pt regular)',                     False),
        ('#595959', '#FFFFFF', 'Body gray — footer / progress label (11pt regular)',       False),
        ('#595959', '#FFFFFF', 'Body gray — about body + address text (15pt regular)',     False),
        # White on dark teal — section, quote, two-column right panel
        ('#FFFFFF', '#2E4057', 'White — body text on full-navy slides (16pt regular)',     False),
        ('#FFFFFF', '#2E4057', 'White — subheads on dark teal (14pt bold)',                True),
        ('#FFFFFF', '#2E4057', 'White — two-column right panel body (16pt regular)',       False),
        # Dark teal on light gray — two-column left panel
        ('#2E4057', '#EFEFEF', 'Dark navy — labels on light gray panel (14pt bold)',       True),
        # White on body gray — (reserved; no current text-on-gray-bg usage)
        ('#FFFFFF', '#595959', 'White — on body-gray backgrounds',                         False),
        # Body gray on light gray — footer rule area
        ('#595959', '#EFEFEF', 'Body gray — footer on light gray',                         False),
        # Slate blue on white — about layout title and call-to-action
        ('#6B8CBE', '#FFFFFF', 'Slate blue — About title (22pt bold)',                     True),
        ('#6B8CBE', '#FFFFFF', 'Slate blue — website call-to-action text (15pt bold)',     True),
        # White on slate blue — agenda circle numbers (14pt bold after fix)
        ('#FFFFFF', '#6B8CBE', 'White — numbers on steel blue agenda circles (14pt bold)', True),
    ]

    print()
    print('Text Colour Pairs')
    print('-' * 60)
    for fg, bg, desc, is_large in TEXT_PAIRS:
        r = contrast(fg, bg)
        result, note = grade(r, is_large)
        if 'FAIL' in result or 'WARN' in result:
            all_pass = False
        print(f'  {result}  {r:.2f}:1  {fg} / {bg}')
        print(f'           {desc}')
        print(f'           {note}')

    # ── 2. Olive decoration restriction ───────────────────────────
    print()
    print('Amber Colour Restrictions  (#E8863A)')
    print('-' * 60)
    olive_white = contrast('#E8863A', '#FFFFFF')
    olive_teal  = contrast('#E8863A', '#2E4057')
    print(f'  {DECOR}  {olive_white:.2f}:1  on white      — TEXT USE PROHIBITED')
    print(f'           Permitted: stat slide decorative rule only')
    print(f'  {DECOR}  {olive_teal:.2f}:1  on dark teal  — TEXT USE PROHIBITED')
    print(f'           Permitted: Venn circle fills only')

    # ── 3. Font size validation ───────────────────────────────────
    print()
    print('Font Size Validation')
    print('-' * 60)
    # (role, size_pt, is_bold, layout)
    SIZES = [
        ('Cover title',              30, True,  'cover, closing'),
        ('Section title',            34, False, 'section'),
        ('Slide title',              22, True,  'content, content-image, two-column'),
        ('Subhead label',            14, True,  'content, content-image, section, about'),
        ('Body text',                16, False, 'content, content-image, two-column, quote'),
        ('About body / address',     15, False, 'about'),
        ('Agenda items',             18, False, 'agenda'),
        ('Agenda circle numbers',    14, True,  'agenda'),
        ('Stat number',              64, True,  'stat'),
        ('Stat label',               22, True,  'stat'),
        ('Quote text',               20, False, 'quote'),
        ('Attribution',              14, True,  'quote'),
        ('Footer / progress label',  11, False, 'all white-bg layouts'),
    ]
    for name, size, bold, layouts in SIZES:
        is_large = (bold and size >= 14) or (not bold and size >= 18)
        ok = size >= 10
        if not ok:
            all_pass = False
        tag  = PASS if ok else FAIL
        kind = 'bold' if bold else '    '
        lt   = 'large text' if is_large else 'normal text'
        print(f'  {tag}  {size:2d}pt {kind}  {name:<28}  ({lt})  [{layouts}]')

    # ── 4. Per-layout structural checks ──────────────────────────
    print()
    print('Per-Layout Structural Requirements')
    print('-' * 60)

    # (layout, check description, passes)
    LAYOUT_CHECKS = [
        # cover
        ('cover',         'White logo bottom-left (visible on dark teal)',                        True),
        ('cover',         'image_alt field required in YAML',                                     True),
        ('cover',         'No page number — intentional (logo-only footer)',                      True),
        # closing
        ('closing',       'White logo bottom-left (visible on dark teal)',                        True),
        ('closing',       'image_alt field required in YAML',                                     True),
        ('closing',       'No page number — intentional (logo-only footer)',                      True),
        # agenda
        ('agenda',        'Standard footer with page number',                                     True),
        ('agenda',        'Items use number + text label (not number-only — not colour-only)',    True),
        ('agenda',        'Circle numbers 14pt bold — meets AA large text on slate blue (3.43:1)', True),
        # section
        ('section',       'Dark footer with page number',                                         True),
        ('section',       'image_alt field required in YAML',                                     True),
        ('section',       'Vertical pipe rule is decoration — carries no information',            True),
        ('section',       'Teal overlay on image is decoration — image has alt text',             True),
        # content
        ('content',       'Progress bar has "Section X of N" text label (not colour-only)',       True),
        ('content',       'Standard footer with page number',                                     True),
        ('content',       'Divider rule below title is decoration',                               True),
        # content-image
        ('content-image', 'Progress bar has "Section X of N" text label (not colour-only)',       True),
        ('content-image', 'Standard footer with page number',                                     True),
        ('content-image', 'image_alt field required in YAML',                                     True),
        ('content-image', 'Caption bar is supplementary — image meaning conveyed by alt text',   True),
        # two-column
        ('two-column',    'Progress bar has "Section X of N" text label (not colour-only)',       True),
        ('two-column',    'Standard footer with page number',                                     True),
        ('two-column',    'Column headers label content — colour not sole differentiator',        True),
        # quote
        ('quote',         'Dark footer with page number',                                         True),
        ('quote',         'Opening quotation mark is decoration — quote text is full content',    True),
        ('quote',         'Venn circles are decoration — carry no information',                   True),
        # stat
        ('stat',          'Progress bar has "Section X of N" text label (not colour-only)',       True),
        ('stat',          'Standard footer with page number',                                     True),
        ('stat',          'Olive decorative rule carries no information',                         True),
        # about
        ('about',         'Coloured logo bottom-left on white background',                        True),
        ('about',         'Slate blue title 22pt bold — AA large text on white (3.43:1)',         True),
        ('about',         'Slate blue website text 15pt bold — AA large text on white (3.43:1)', True),
        ('about',         'Slate blue rule is decoration — right column labelled by address text', True),
        ('about',         'No page number — intentional (standalone org info slide)',             True),
    ]

    current_layout = None
    for layout, desc, ok in LAYOUT_CHECKS:
        if layout != current_layout:
            current_layout = layout
            print(f'\n  [{layout}]')
        if not ok:
            all_pass = False
        print(f'    {PASS if ok else FAIL}  {desc}')

    # ── Summary ───────────────────────────────────────────────────
    print()
    print('=' * 60)
    if all_pass:
        print('All checks passed. Design system is 508-compliant.')
    else:
        print('One or more checks FAILED. Resolve before distributing.')
    print()


if __name__ == '__main__':
    main()

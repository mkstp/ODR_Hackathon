"""chart_utils.py — Render a chart spec dict to a ReportLab ImageReader.

Requires: matplotlib  (pip install matplotlib)

Supported chart types
---------------------
  hbar   Horizontal bar chart (default for ranked/categorical data)
  bar    Vertical bar chart
  line   Line chart (single or multi-series)
  table  Styled data table

Usage from build_slides.py
--------------------------
    from chart_utils import render_chart
    reader = render_chart(slide['chart'], width_pt=IMG_W, height_pt=IMG_H)
    c.drawImage(reader, IMG_X, IMG_Y, width=IMG_W, height=IMG_H, mask='auto')

YAML spec keys (all optional except `type` and `data`)
-------------------------------------------------------
  type     str   'hbar' | 'bar' | 'line' | 'table'
  title    str   Chart title (rendered in dark teal, bold)
  data     list  See per-type notes below
  color    str   'teal' | 'steel' | 'olive' | 'gray'  (single-series only)
  x_label  str   Axis label (bar/line)
  y_label  str   Axis label (bar/line)
  percent  bool  Append '%' to value labels and tick marks (default False)
  source   str   Attribution line rendered bottom-right in small italic gray
  legend   bool  Show legend (multi-series line charts; default True)

Data shapes
-----------
  hbar / bar  list of {label: str, value: float}
  line        single-series: list of {x: str|float, y: float}
              multi-series:  list of {label: str, points: [{x, y}, ...]}
  table       use keys: headers (list of str), rows (list of lists)
"""

import io
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from reportlab.lib.utils import ImageReader

# ── Brand palette — mirrors build_slides.py ───────────────────────────────────
C_TEAL  = '#1B4E6A'
C_STEEL = '#5A9AB5'
C_OLIVE = '#8FAF3F'
C_GRAY  = '#595959'
C_LIGHT = '#EFEFEF'

COLOR_MAP = {
    'teal':  C_TEAL,
    'steel': C_STEEL,
    'olive': C_OLIVE,
    'gray':  C_GRAY,
}

_STYLE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'cbi.mplstyle')
)


def _style_context():
    if os.path.exists(_STYLE_PATH):
        return plt.style.context(_STYLE_PATH)
    return plt.style.context('default')


def _fig_to_reader(fig, dpi):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return ImageReader(buf)


def _pt_to_in(pt):
    return pt / 72.0


def render_chart(spec, width_pt=361, height_pt=504, dpi=150):
    """Return a ReportLab ImageReader for the chart described by `spec`."""
    chart_type = spec.get('type', 'hbar')
    dispatch = {
        'hbar':  _render_bar,
        'bar':   _render_bar,
        'line':  _render_line,
        'table': _render_table,
    }
    fn = dispatch.get(chart_type, _render_bar)
    return fn(spec, width_pt, height_pt, dpi)


# ── Bar / Horizontal bar ──────────────────────────────────────────────────────

def _render_bar(spec, width_pt, height_pt, dpi):
    horizontal = spec.get('type', 'hbar') == 'hbar'
    data       = spec.get('data', [])
    labels     = [str(d.get('label', '')) for d in data]
    values     = [float(d.get('value', 0)) for d in data]
    color      = COLOR_MAP.get(spec.get('color', 'teal'), C_TEAL)
    title      = spec.get('title', '')
    source     = spec.get('source', '')
    percent    = spec.get('percent', False)

    if not values:
        return _empty_reader(width_pt, height_pt, dpi)

    max_val = max(values)

    with _style_context():
        fig, ax = plt.subplots(figsize=(_pt_to_in(width_pt), _pt_to_in(height_pt)))

        if horizontal:
            bars = ax.barh(labels, values, color=color, height=0.55)
            ax.set_xlim(0, max_val * 1.2)
            ax.xaxis.set_major_formatter(
                mticker.FuncFormatter(lambda v, _: f'{v:.0f}%' if percent else f'{v:.0f}')
            )
            ax.spines['left'].set_visible(False)
            ax.tick_params(axis='y', length=0)
            ax.invert_yaxis()
            ax.grid(True, axis='x')

            for bar, val in zip(bars, values):
                label_str = f'{val:.0f}%' if percent else f'{val:.0f}'
                ax.text(
                    val + max_val * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    label_str,
                    va='center', ha='left',
                    color=C_TEAL, fontsize=10, fontweight='bold',
                )
        else:
            bars = ax.bar(labels, values, color=color, width=0.55)
            ax.set_ylim(0, max_val * 1.2)
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda v, _: f'{v:.0f}%' if percent else f'{v:.0f}')
            )
            ax.spines['bottom'].set_visible(True)
            ax.grid(True, axis='y')

            for bar, val in zip(bars, values):
                label_str = f'{val:.0f}%' if percent else f'{val:.0f}'
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    val + max_val * 0.01,
                    label_str,
                    ha='center', va='bottom',
                    color=C_TEAL, fontsize=10, fontweight='bold',
                )

        if title:
            ax.set_title(title, color=C_TEAL, loc='left')
        if spec.get('x_label'):
            ax.set_xlabel(spec['x_label'])
        if spec.get('y_label'):
            ax.set_ylabel(spec['y_label'])
        if source:
            fig.text(0.98, 0.02, f'Source: {source}',
                     ha='right', va='bottom', fontsize=8,
                     color='#9A9A9A', style='italic')

        fig.tight_layout(rect=[0, 0.08 if source else 0, 1, 1])

    return _fig_to_reader(fig, dpi)


# ── Line chart ────────────────────────────────────────────────────────────────

def _render_line(spec, width_pt, height_pt, dpi):
    data    = spec.get('data', [])
    title   = spec.get('title', '')
    source  = spec.get('source', '')
    percent = spec.get('percent', False)
    show_legend = spec.get('legend', True)

    if not data:
        return _empty_reader(width_pt, height_pt, dpi)

    # Detect multi-series vs single-series
    multi = isinstance(data[0], dict) and 'points' in data[0]

    with _style_context():
        fig, ax = plt.subplots(figsize=(_pt_to_in(width_pt), _pt_to_in(height_pt)))

        if multi:
            for series in data:
                pts = series.get('points', [])
                xs  = [p.get('x', i) for i, p in enumerate(pts)]
                ys  = [float(p.get('y', 0)) for p in pts]
                ax.plot(xs, ys, marker='o', markersize=5, label=series.get('label', ''))
            if show_legend:
                ax.legend()
        else:
            xs = [d.get('x', i) for i, d in enumerate(data)]
            ys = [float(d.get('y', 0)) for d in data]
            color = COLOR_MAP.get(spec.get('color', 'teal'), C_TEAL)
            ax.plot(xs, ys, color=color, marker='o', markersize=5)

        ax.grid(True, axis='y')

        if percent:
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda v, _: f'{v:.0f}%')
            )

        if title:
            ax.set_title(title, color=C_TEAL, loc='left')
        if spec.get('x_label'):
            ax.set_xlabel(spec['x_label'])
        if spec.get('y_label'):
            ax.set_ylabel(spec['y_label'])
        if source:
            fig.text(0.98, 0.02, f'Source: {source}',
                     ha='right', va='bottom', fontsize=8,
                     color='#9A9A9A', style='italic')

        fig.tight_layout(rect=[0, 0.08 if source else 0, 1, 1])

    return _fig_to_reader(fig, dpi)


# ── Table ─────────────────────────────────────────────────────────────────────

def _render_table(spec, width_pt, height_pt, dpi):
    headers = spec.get('headers', [])
    rows    = spec.get('rows', [])
    title   = spec.get('title', '')
    source  = spec.get('source', '')

    if not rows:
        return _empty_reader(width_pt, height_pt, dpi)

    with _style_context():
        fig, ax = plt.subplots(figsize=(_pt_to_in(width_pt), _pt_to_in(height_pt)))
        ax.axis('off')

        tbl = ax.table(
            cellText=rows,
            colLabels=headers if headers else None,
            cellLoc='left',
            loc='center',
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(10)
        tbl.scale(1, 1.8)
        tbl.auto_set_column_width(col=list(range(len(headers or rows[0]))))

        for (row, col), cell in tbl.get_celld().items():
            cell.set_edgecolor(C_LIGHT)
            cell.PAD = 0.08
            if row == 0 and headers:
                cell.set_facecolor(C_TEAL)
                cell.get_text().set_color('white')
                cell.get_text().set_fontweight('bold')
            elif row % 2 == 0:
                cell.set_facecolor('#F7F7F7')
            else:
                cell.set_facecolor('white')

        if title:
            ax.set_title(title, color=C_TEAL, loc='left', pad=14)
        if source:
            fig.text(0.98, 0.02, f'Source: {source}',
                     ha='right', va='bottom', fontsize=8,
                     color='#9A9A9A', style='italic')

        fig.tight_layout(rect=[0, 0.08 if source else 0, 1, 1])

    return _fig_to_reader(fig, dpi)


# ── Fallback ──────────────────────────────────────────────────────────────────

def _empty_reader(width_pt, height_pt, dpi):
    with _style_context():
        fig, ax = plt.subplots(figsize=(_pt_to_in(width_pt), _pt_to_in(height_pt)))
        ax.text(0.5, 0.5, '[No data]', ha='center', va='center',
                transform=ax.transAxes, color=C_GRAY, fontsize=12)
        ax.axis('off')
    return _fig_to_reader(fig, dpi)

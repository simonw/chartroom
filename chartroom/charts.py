import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Optional
import numpy as np


def _apply_style(style: Optional[str]):
    """Apply a matplotlib style if specified."""
    if style:
        plt.style.use(style)
    else:
        plt.style.use("default")


def _make_figure(width: float, height: float) -> tuple:
    """Create a figure and axes with the given dimensions."""
    fig, ax = plt.subplots(figsize=(width, height))
    return fig, ax


def _finalize(
    fig,
    ax,
    output_path: str,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    dpi: int = 100,
    show_legend: bool = False,
):
    """Apply labels, save, and close the figure."""
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if show_legend:
        ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)


def _to_float(values: list, col_name: str) -> list:
    """Convert values to float, raising a clear error on failure."""
    result = []
    for v in values:
        try:
            result.append(float(v))
        except (ValueError, TypeError):
            raise ValueError(
                f"Cannot convert value {v!r} in column '{col_name}' to a number"
            )
    return result


def render_bar(
    rows: List[Dict[str, Any]],
    x_col: str,
    y_cols: List[str],
    output_path: str,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    width: float = 10,
    height: float = 6,
    style: Optional[str] = None,
    dpi: int = 100,
):
    _apply_style(style)
    fig, ax = _make_figure(width, height)

    x_labels = [str(row[x_col]) for row in rows]
    x_pos = np.arange(len(x_labels))

    if len(y_cols) == 1:
        values = _to_float([row[y_cols[0]] for row in rows], y_cols[0])
        ax.bar(x_pos, values)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(x_labels)
    else:
        n_series = len(y_cols)
        bar_width = 0.8 / n_series
        for i, yc in enumerate(y_cols):
            values = _to_float([row[yc] for row in rows], yc)
            offset = (i - n_series / 2 + 0.5) * bar_width
            ax.bar(x_pos + offset, values, bar_width, label=yc)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(x_labels)

    _finalize(
        fig, ax, output_path, title, xlabel, ylabel, dpi, show_legend=len(y_cols) > 1
    )


def render_line(
    rows: List[Dict[str, Any]],
    x_col: str,
    y_cols: List[str],
    output_path: str,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    width: float = 10,
    height: float = 6,
    style: Optional[str] = None,
    dpi: int = 100,
):
    _apply_style(style)
    fig, ax = _make_figure(width, height)

    x_labels = [str(row[x_col]) for row in rows]
    x_pos = range(len(x_labels))

    for yc in y_cols:
        values = _to_float([row[yc] for row in rows], yc)
        ax.plot(x_pos, values, label=yc, marker="o")

    ax.set_xticks(list(x_pos))
    ax.set_xticklabels(x_labels)

    _finalize(
        fig, ax, output_path, title, xlabel, ylabel, dpi, show_legend=len(y_cols) > 1
    )


def render_scatter(
    rows: List[Dict[str, Any]],
    x_col: str,
    y_cols: List[str],
    output_path: str,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    width: float = 10,
    height: float = 6,
    style: Optional[str] = None,
    dpi: int = 100,
):
    _apply_style(style)
    fig, ax = _make_figure(width, height)

    x_values = _to_float([row[x_col] for row in rows], x_col)

    for yc in y_cols:
        y_values = _to_float([row[yc] for row in rows], yc)
        ax.scatter(x_values, y_values, label=yc)

    _finalize(
        fig, ax, output_path, title, xlabel, ylabel, dpi, show_legend=len(y_cols) > 1
    )


def render_pie(
    rows: List[Dict[str, Any]],
    x_col: str,
    y_col: str,
    output_path: str,
    title: Optional[str] = None,
    width: float = 10,
    height: float = 6,
    style: Optional[str] = None,
    dpi: int = 100,
):
    _apply_style(style)
    fig, ax = _make_figure(width, height)

    labels = [str(row[x_col]) for row in rows]
    values = _to_float([row[y_col] for row in rows], y_col)

    ax.pie(values, labels=labels, autopct="%1.1f%%")

    if title:
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)


def render_histogram(
    rows: List[Dict[str, Any]],
    y_col: str,
    output_path: str,
    bins: int = 10,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    width: float = 10,
    height: float = 6,
    style: Optional[str] = None,
    dpi: int = 100,
):
    _apply_style(style)
    fig, ax = _make_figure(width, height)

    values = _to_float([row[y_col] for row in rows], y_col)
    ax.hist(values, bins=bins)

    _finalize(fig, ax, output_path, title, xlabel, ylabel, dpi)

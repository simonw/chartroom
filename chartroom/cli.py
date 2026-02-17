import html as html_mod
import json as json_mod
import os
import sqlite3
import sys

import click

from chartroom.io import load_rows, resolve_columns
from chartroom.charts import (
    render_bar,
    render_line,
    render_scatter,
    render_pie,
    render_histogram,
    render_radar,
)


def _fmt_num(val):
    """Format a number: drop trailing .0 for clean display."""
    if isinstance(val, float) and val == int(val):
        return str(int(val))
    return str(val)


def _generate_alt_text(chart_type, rows, x_col, y_cols, title=None):
    """Generate descriptive alt text based on chart data.

    If title is set, it is prepended: "Title. Generated description".
    """
    description = _describe_chart(chart_type, rows, x_col, y_cols)
    if title:
        return f"{title}. {description}"
    return description


def _describe_chart(chart_type, rows, x_col, y_cols):
    """Build a data-driven description of the chart."""
    type_labels = {
        "bar": "Bar chart",
        "line": "Line chart",
        "scatter": "Scatter plot",
        "pie": "Pie chart",
        "histogram": "Histogram",
        "radar": "Radar chart",
    }
    label = type_labels.get(chart_type, "Chart")
    n = len(rows)

    if chart_type == "histogram":
        col = y_cols[0] if y_cols else "values"
        vals = []
        for r in rows:
            try:
                vals.append(float(r[col]))
            except (ValueError, TypeError, KeyError):
                continue
        if vals:
            lo, hi = min(vals), max(vals)
            if n <= 6:
                formatted = ", ".join(_fmt_num(v) for v in vals)
                return f"{label} of {col} values: {formatted}"
            return (
                f"{label} of {len(vals)} {col} values "
                f"ranging from {_fmt_num(lo)} to {_fmt_num(hi)}"
            )
        return f"{label} of {col}"

    if chart_type == "pie":
        y_col = y_cols[0] if y_cols else None
        if x_col and y_col:
            pairs = []
            for r in rows:
                try:
                    pairs.append((r[x_col], float(r[y_col])))
                except (ValueError, TypeError, KeyError):
                    continue
            if pairs:
                total = sum(v for _, v in pairs)
                if n <= 6 and total > 0:
                    parts = []
                    for name, val in pairs:
                        pct = val / total * 100
                        parts.append(f"{name} ({pct:.0f}%)")
                    return f"{label} showing {', '.join(parts)}"
                elif total > 0:
                    sorted_pairs = sorted(pairs, key=lambda p: p[1], reverse=True)
                    top = sorted_pairs[:3]
                    parts = []
                    for name, val in top:
                        pct = val / total * 100
                        parts.append(f"{name} ({pct:.0f}%)")
                    return f"{label} of {n} categories. " f"Largest: {', '.join(parts)}"
        return f"{label} of {x_col or 'categories'}"

    # bar, line, scatter — numeric y columns
    if x_col and y_cols:
        for y_col in y_cols[:1]:
            vals = []
            for r in rows:
                try:
                    vals.append((r.get(x_col, ""), float(r[y_col])))
                except (ValueError, TypeError, KeyError):
                    continue
            if not vals:
                continue

            y_values = [v for _, v in vals]
            lo, hi = min(y_values), max(y_values)

            if n <= 6:
                parts = [f"{name}: {_fmt_num(val)}" for name, val in vals]
                series_note = ""
                if len(y_cols) > 1:
                    series_note = f" and {len(y_cols) - 1} more series"
                return (
                    f"{label} of {y_col} by {x_col} \u2014 "
                    f"{', '.join(parts)}{series_note}"
                )
            else:
                max_pair = max(vals, key=lambda p: p[1])
                min_pair = min(vals, key=lambda p: p[1])
                series_note = ""
                if len(y_cols) > 1:
                    series_note = f" ({len(y_cols)} series)"
                return (
                    f"{label} of {y_col} by {x_col}{series_note}. "
                    f"{n} points, ranging from {_fmt_num(lo)} ({min_pair[0]}) "
                    f"to {_fmt_num(hi)} ({max_pair[0]})"
                )

    return label


def _format_output(output_path, fmt, alt_text):
    """Format the output according to the chosen output format."""
    if fmt == "markdown":
        return f"![{alt_text}]({output_path})"
    elif fmt == "html":
        escaped_alt = html_mod.escape(alt_text, quote=True)
        return f'<img src="{output_path}" alt="{escaped_alt}">'
    elif fmt == "json":
        return json_mod.dumps({"path": output_path, "alt": alt_text})
    elif fmt == "alt":
        return alt_text
    return output_path


def _resolve_output(output: str | None) -> str:
    """Resolve the output file path, auto-generating if needed."""
    if output:
        return os.path.abspath(output)

    # Auto-generate: chart.png, chart-2.png, chart-3.png, ...
    candidate = "chart.png"
    counter = 2
    while os.path.exists(candidate):
        candidate = f"chart-{counter}.png"
        counter += 1
    return os.path.abspath(candidate)


def _load_data(file, csv, tsv, json, jsonl, sql):
    """Load data from the various input sources."""
    sql_db = None
    sql_query = None
    fmt = None
    fp = None

    if sql:
        if len(sql) != 2:
            raise click.UsageError(
                "--sql requires exactly two arguments: DATABASE QUERY"
            )
        sql_db, sql_query = sql
        if csv or tsv or json or jsonl:
            raise click.UsageError(
                "--sql cannot be combined with --csv/--tsv/--json/--jsonl"
            )
        if file is not None:
            raise click.UsageError("--sql cannot be combined with a FILE argument")
    else:
        if sum([csv, tsv, json, jsonl]) > 1:
            raise click.UsageError(
                "Specify at most one of --csv, --tsv, --json, --jsonl"
            )
        if csv:
            fmt = "csv"
        elif tsv:
            fmt = "tsv"
        elif json:
            fmt = "json"
        elif jsonl:
            fmt = "jsonl"
        # else: auto-detect

        if file is not None:
            fp = click.open_file(file, "rb")
        else:
            # Try reading from stdin
            stdin = click.get_binary_stream("stdin")
            if hasattr(stdin, "isatty") and stdin.isatty():
                raise click.UsageError(
                    "Provide a FILE argument, pipe data to stdin, or use --sql"
                )
            fp = stdin

    return load_rows(fp=fp, format=fmt, sql_db=sql_db, sql_query=sql_query)


# Shared options applied to all chart subcommands
_common_options = [
    click.argument("file", required=False, default=None),
    click.option(
        "-o", "--output", default=None, help="Output file path (default: chart.png)"
    ),
    click.option("-x", default=None, help="Column for x-axis / categories"),
    click.option(
        "-y", multiple=True, help="Column(s) for y-axis / values (repeatable)"
    ),
    click.option("--csv", "csv", is_flag=True, help="Parse input as CSV"),
    click.option("--tsv", "tsv", is_flag=True, help="Parse input as TSV"),
    click.option("--json", "json", is_flag=True, help="Parse input as JSON"),
    click.option(
        "--jsonl", "jsonl", is_flag=True, help="Parse input as newline-delimited JSON"
    ),
    click.option(
        "--sql",
        nargs=2,
        default=None,
        help=(
            "Query a SQLite database. Takes two arguments: DATABASE QUERY. "
            "Example: --sql mydb.sqlite 'SELECT name, count FROM items'"
        ),
    ),
    click.option(
        "--title", default=None, help="Chart title, also prepended to generated alt text"
    ),
    click.option("--xlabel", default=None, help="X-axis label"),
    click.option("--ylabel", default=None, help="Y-axis label"),
    click.option("--width", default=10.0, type=float, help="Figure width in inches"),
    click.option("--height", default=6.0, type=float, help="Figure height in inches"),
    click.option(
        "--style", default=None, help="Matplotlib style (e.g. ggplot, dark_background)"
    ),
    click.option("--dpi", default=100, type=int, help="Output DPI"),
    click.option(
        "-f",
        "--output-format",
        "output_format",
        default="path",
        type=click.Choice(["path", "markdown", "html", "json", "alt"]),
        help=(
            "How to format stdout. "
            "path (default): absolute file path. "
            "markdown: ![alt](path). "
            "html: <img src=path alt=...>. "
            "json: {\"path\": ..., \"alt\": ...}. "
            "alt: just the alt text, no path. "
            "Alt text is auto-generated from chart type and data unless --alt is given."
        ),
    ),
    click.option(
        "--alt",
        default=None,
        help=(
            "Override the auto-generated alt text. "
            "Ignored when -f is path (the default). "
            "When omitted, a description is generated from the chart type "
            "and data."
        ),
    ),
]


def common_options(fn):
    for decorator in reversed(_common_options):
        fn = decorator(fn)
    return fn


@click.group()
@click.version_option()
def cli():
    "CLI tool for creating charts"


def _run_chart(
    chart_type,
    render_fn,
    file,
    output,
    x,
    y,
    csv,
    tsv,
    json,
    jsonl,
    sql,
    title,
    xlabel,
    ylabel,
    width,
    height,
    style,
    dpi,
    **extra,
):
    """Common logic for all chart subcommands."""
    output_format = extra.pop("output_format", "path")
    alt = extra.pop("alt", None)
    try:
        rows = _load_data(file, csv, tsv, json, jsonl, sql)
        x_col, y_cols = resolve_columns(rows, x, y, chart_type=chart_type)
        output_path = _resolve_output(output)
        render_fn(
            rows=rows,
            x_col=x_col,
            y_cols=y_cols,
            output_path=output_path,
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            width=width,
            height=height,
            style=style,
            dpi=dpi,
            **extra,
        )
        if output_format == "path":
            click.echo(output_path)
        else:
            alt_text = alt or _generate_alt_text(
                chart_type, rows, x_col, y_cols, title=title
            )
            click.echo(_format_output(output_path, output_format, alt_text))
    except click.UsageError:
        raise
    except (ValueError, sqlite3.OperationalError) as e:
        raise click.ClickException(str(e))


def _render_bar_wrapper(rows, x_col, y_cols, output_path, **kwargs):
    render_bar(rows, x_col, y_cols, output_path, **kwargs)


def _render_line_wrapper(rows, x_col, y_cols, output_path, **kwargs):
    render_line(rows, x_col, y_cols, output_path, **kwargs)


def _render_scatter_wrapper(rows, x_col, y_cols, output_path, **kwargs):
    render_scatter(rows, x_col, y_cols, output_path, **kwargs)


def _render_pie_wrapper(
    rows, x_col, y_cols, output_path, xlabel=None, ylabel=None, **kwargs
):
    # Pie charts ignore xlabel/ylabel
    render_pie(rows, x_col, y_cols[0], output_path, **kwargs)


def _render_histogram_wrapper(rows, x_col, y_cols, output_path, bins=10, **kwargs):
    render_histogram(rows, y_cols[0], output_path, bins=bins, **kwargs)


def _render_radar_wrapper(
    rows, x_col, y_cols, output_path, xlabel=None, ylabel=None, **kwargs
):
    # Radar charts ignore xlabel/ylabel
    render_radar(rows, x_col, y_cols, output_path, **kwargs)


@cli.command()
@common_options
def bar(
    file,
    output,
    x,
    y,
    csv,
    tsv,
    json,
    jsonl,
    sql,
    title,
    xlabel,
    ylabel,
    width,
    height,
    style,
    dpi,
    output_format,
    alt,
):
    """Create a bar chart from columnar data.

    \b
    Examples:
      chartroom bar --csv data.csv
      chartroom bar --csv data.csv -x region -y revenue -o sales.png
      chartroom bar --csv -x name -y q1 -y q2 data.csv
      cat data.csv | chartroom bar --csv -f markdown
      chartroom bar --sql mydb.sqlite "SELECT name, count FROM items"
    """
    _run_chart(
        "bar",
        _render_bar_wrapper,
        file,
        output,
        x,
        y,
        csv,
        tsv,
        json,
        jsonl,
        sql,
        title,
        xlabel,
        ylabel,
        width,
        height,
        style,
        dpi,
        output_format=output_format,
        alt=alt,
    )


@cli.command()
@common_options
def line(
    file,
    output,
    x,
    y,
    csv,
    tsv,
    json,
    jsonl,
    sql,
    title,
    xlabel,
    ylabel,
    width,
    height,
    style,
    dpi,
    output_format,
    alt,
):
    """Create a line chart from columnar data.

    \b
    Examples:
      chartroom line --csv data.csv
      chartroom line --csv data.csv -x month -y revenue
      chartroom line --csv -x date -y temp -y humidity data.csv
      chartroom line --csv data.csv -f json
    """
    _run_chart(
        "line",
        _render_line_wrapper,
        file,
        output,
        x,
        y,
        csv,
        tsv,
        json,
        jsonl,
        sql,
        title,
        xlabel,
        ylabel,
        width,
        height,
        style,
        dpi,
        output_format=output_format,
        alt=alt,
    )


@cli.command()
@common_options
def scatter(
    file,
    output,
    x,
    y,
    csv,
    tsv,
    json,
    jsonl,
    sql,
    title,
    xlabel,
    ylabel,
    width,
    height,
    style,
    dpi,
    output_format,
    alt,
):
    """Create a scatter plot from columnar data.

    \b
    Examples:
      chartroom scatter --csv data.csv
      chartroom scatter --csv data.csv -x height -y weight
      chartroom scatter --csv data.csv -f html --alt "Height vs Weight"
    """
    _run_chart(
        "scatter",
        _render_scatter_wrapper,
        file,
        output,
        x,
        y,
        csv,
        tsv,
        json,
        jsonl,
        sql,
        title,
        xlabel,
        ylabel,
        width,
        height,
        style,
        dpi,
        output_format=output_format,
        alt=alt,
    )


@cli.command()
@common_options
def pie(
    file,
    output,
    x,
    y,
    csv,
    tsv,
    json,
    jsonl,
    sql,
    title,
    xlabel,
    ylabel,
    width,
    height,
    style,
    dpi,
    output_format,
    alt,
):
    """Create a pie chart from columnar data.

    Uses the first -y column for slice sizes. Labels come from the -x column.

    \b
    Examples:
      chartroom pie --csv data.csv
      chartroom pie --csv data.csv -x category -y amount
      chartroom pie --csv data.csv -f markdown
    """
    _run_chart(
        "pie",
        _render_pie_wrapper,
        file,
        output,
        x,
        y,
        csv,
        tsv,
        json,
        jsonl,
        sql,
        title,
        xlabel,
        ylabel,
        width,
        height,
        style,
        dpi,
        output_format=output_format,
        alt=alt,
    )


@cli.command()
@common_options
@click.option("--bins", default=10, type=int, help="Number of histogram bins")
def histogram(
    file,
    output,
    x,
    y,
    csv,
    tsv,
    json,
    jsonl,
    sql,
    title,
    xlabel,
    ylabel,
    width,
    height,
    style,
    dpi,
    bins,
    output_format,
    alt,
):
    """Create a histogram showing the distribution of a numeric column.

    Requires -y to specify the column. Use --bins to control bucket count.

    \b
    Examples:
      chartroom histogram --csv -y score data.csv
      chartroom histogram --csv -y score data.csv --bins 20
      chartroom histogram --csv -y score data.csv -f alt
    """
    _run_chart(
        "histogram",
        _render_histogram_wrapper,
        file,
        output,
        x,
        y,
        csv,
        tsv,
        json,
        jsonl,
        sql,
        title,
        xlabel,
        ylabel,
        width,
        height,
        style,
        dpi,
        bins=bins,
        output_format=output_format,
        alt=alt,
    )


@cli.command()
@common_options
@click.option(
    "--fill/--no-fill", default=True, help="Fill the radar polygons (default: fill)"
)
def radar(
    file,
    output,
    x,
    y,
    csv,
    tsv,
    json,
    jsonl,
    sql,
    title,
    xlabel,
    ylabel,
    width,
    height,
    style,
    dpi,
    fill,
    output_format,
    alt,
):
    """Create a radar (spider) chart from columnar data.

    Each row is one axis of the radar. The -x column provides axis labels,
    and each -y column is a series plotted on the radar.

    \b
    Examples:
      chartroom radar --csv data.csv
      chartroom radar --csv data.csv -x attribute -y player1 -y player2
      chartroom radar --csv data.csv --no-fill -f markdown
    """
    _run_chart(
        "radar",
        _render_radar_wrapper,
        file,
        output,
        x,
        y,
        csv,
        tsv,
        json,
        jsonl,
        sql,
        title,
        xlabel,
        ylabel,
        width,
        height,
        style,
        dpi,
        fill=fill,
        output_format=output_format,
        alt=alt,
    )


@cli.command()
def styles():
    """List available matplotlib styles."""
    import matplotlib.pyplot as plt

    for style in sorted(plt.style.available):
        if not style.startswith("_"):
            click.echo(style)

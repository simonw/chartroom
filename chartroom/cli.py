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
)


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
            raise click.UsageError("--sql requires exactly two arguments: DATABASE QUERY")
        sql_db, sql_query = sql
        if csv or tsv or json or jsonl:
            raise click.UsageError("--sql cannot be combined with --csv/--tsv/--json/--jsonl")
        if file is not None:
            raise click.UsageError("--sql cannot be combined with a FILE argument")
    else:
        if sum([csv, tsv, json, jsonl]) > 1:
            raise click.UsageError("Specify at most one of --csv, --tsv, --json, --jsonl")
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
    click.option("-o", "--output", default=None, help="Output file path (default: chart.png)"),
    click.option("-x", default=None, help="Column for x-axis / categories"),
    click.option("-y", multiple=True, help="Column(s) for y-axis / values (repeatable)"),
    click.option("--csv", "csv", is_flag=True, help="Parse input as CSV"),
    click.option("--tsv", "tsv", is_flag=True, help="Parse input as TSV"),
    click.option("--json", "json", is_flag=True, help="Parse input as JSON"),
    click.option("--jsonl", "jsonl", is_flag=True, help="Parse input as newline-delimited JSON"),
    click.option("--sql", nargs=2, default=None, help="DATABASE QUERY - query a SQLite database"),
    click.option("--title", default=None, help="Chart title"),
    click.option("--xlabel", default=None, help="X-axis label"),
    click.option("--ylabel", default=None, help="Y-axis label"),
    click.option("--width", default=10.0, type=float, help="Figure width in inches"),
    click.option("--height", default=6.0, type=float, help="Figure height in inches"),
    click.option("--style", default=None, help="Matplotlib style (e.g. ggplot, dark_background)"),
    click.option("--dpi", default=100, type=int, help="Output DPI"),
]


def common_options(fn):
    for decorator in reversed(_common_options):
        fn = decorator(fn)
    return fn


@click.group()
@click.version_option()
def cli():
    "CLI tool for creating charts"


def _run_chart(chart_type, render_fn, file, output, x, y, csv, tsv, json, jsonl, sql,
               title, xlabel, ylabel, width, height, style, dpi, **extra):
    """Common logic for all chart subcommands."""
    try:
        rows = _load_data(file, csv, tsv, json, jsonl, sql)
        x_col, y_cols = resolve_columns(rows, x, y, chart_type=chart_type)
        output_path = _resolve_output(output)
        render_fn(rows=rows, x_col=x_col, y_cols=y_cols, output_path=output_path,
                  title=title, xlabel=xlabel, ylabel=ylabel,
                  width=width, height=height, style=style, dpi=dpi, **extra)
        click.echo(output_path)
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


def _render_pie_wrapper(rows, x_col, y_cols, output_path, xlabel=None, ylabel=None, **kwargs):
    # Pie charts ignore xlabel/ylabel
    render_pie(rows, x_col, y_cols[0], output_path, **kwargs)


def _render_histogram_wrapper(rows, x_col, y_cols, output_path, bins=10, **kwargs):
    render_histogram(rows, y_cols[0], output_path, bins=bins, **kwargs)


@cli.command()
@common_options
def bar(file, output, x, y, csv, tsv, json, jsonl, sql, title, xlabel, ylabel, width, height, style, dpi):
    "Create a bar chart"
    _run_chart("bar", _render_bar_wrapper, file, output, x, y, csv, tsv, json, jsonl, sql,
               title, xlabel, ylabel, width, height, style, dpi)


@cli.command()
@common_options
def line(file, output, x, y, csv, tsv, json, jsonl, sql, title, xlabel, ylabel, width, height, style, dpi):
    "Create a line chart"
    _run_chart("line", _render_line_wrapper, file, output, x, y, csv, tsv, json, jsonl, sql,
               title, xlabel, ylabel, width, height, style, dpi)


@cli.command()
@common_options
def scatter(file, output, x, y, csv, tsv, json, jsonl, sql, title, xlabel, ylabel, width, height, style, dpi):
    "Create a scatter plot"
    _run_chart("scatter", _render_scatter_wrapper, file, output, x, y, csv, tsv, json, jsonl, sql,
               title, xlabel, ylabel, width, height, style, dpi)


@cli.command()
@common_options
def pie(file, output, x, y, csv, tsv, json, jsonl, sql, title, xlabel, ylabel, width, height, style, dpi):
    "Create a pie chart"
    _run_chart("pie", _render_pie_wrapper, file, output, x, y, csv, tsv, json, jsonl, sql,
               title, xlabel, ylabel, width, height, style, dpi)


@cli.command()
@common_options
@click.option("--bins", default=10, type=int, help="Number of histogram bins")
def histogram(file, output, x, y, csv, tsv, json, jsonl, sql, title, xlabel, ylabel, width, height, style, dpi, bins):
    "Create a histogram"
    _run_chart("histogram", _render_histogram_wrapper, file, output, x, y, csv, tsv, json, jsonl, sql,
               title, xlabel, ylabel, width, height, style, dpi, bins=bins)

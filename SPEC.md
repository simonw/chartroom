# Chartroom Specification

## Overview

Chartroom is a Python CLI tool that uses matplotlib to generate PNG chart images from CSV, TSV, JSON, or SQLite data. It provides subcommands for different chart types with consistent options across all commands.

## Installation

```bash
pip install chartroom
```

Dependencies: `click`, `matplotlib`

## Global Behavior

### Output File Handling

- `-o / --output FILENAME` - Write to specified path. **Overwrites** if file exists.
- If `-o` is not provided, auto-generates filenames: `chart.png`, `chart-2.png`, `chart-3.png`, etc. (never overwrites).
- The tool **always prints the full absolute path** of the generated file to stdout, followed by a newline. This is the only stdout output (so it works with `showboat image`).

### Data Input (consistent across all subcommands)

Three mutually exclusive input modes:

1. **File argument**: `chartroom bar data.csv` — reads from a file
2. **Stdin**: `cat data.csv | chartroom bar` — reads from stdin when no file argument given
3. **SQL mode**: `chartroom bar --sql db.sqlite "SELECT name, count FROM t"` — queries a SQLite database in **read-only** mode (`?mode=ro` URI)

### Format Flags (for file/stdin modes)

Exactly one of these must be provided when using file/stdin input:

- `--csv` — Parse as CSV
- `--tsv` — Parse as TSV
- `--json` — Parse as JSON (expects array of objects: `[{"name": "a", "value": 1}, ...]`)

Not required (and not allowed) when using `--sql`.

### Column Selection

- `-x COLUMN` — Column name for x-axis / categories
- `-y COLUMN` — Column name for y-axis / values. Can be specified multiple times for multi-series charts (line, bar, scatter).

**Auto-detection when `-x` / `-y` are omitted:**

1. If columns named `name` or `label` exist, use as x. If `value` or `count` exist, use as y.
2. Otherwise: first column → x, second column → y.
3. For multi-column data without explicit `-y`, only the second column is used as y (user must explicitly request more with multiple `-y` flags).

### Output Format

- `-f` / `--output-format FORMAT` — Controls what is printed to stdout. Choices:
  - `path` (default) — Print the absolute file path (current behavior)
  - `markdown` — Markdown image syntax: `![alt text](/path/to/chart.png)`
  - `html` — HTML image tag: `<img src="/path/to/chart.png" alt="alt text">`
  - `json` — JSON object: `{"path": "/path/to/chart.png", "alt": "alt text"}`
  - `alt` — Just the alt text string, no path

- `--alt TEXT` — Provide explicit alt text. When omitted, alt text is auto-generated:
  1. If `--title` is set, the title is used as alt text
  2. Otherwise, a description is generated from the chart type and data:
     - Small datasets (≤6 items): lists all values (e.g. "Bar chart of value by name — alice: 10, bob: 20, charlie: 15")
     - Large datasets: summarizes range and extremes (e.g. "Bar chart of value by name. 20 points, ranging from 0 (item0) to 190 (item19)")
     - Pie charts: shows percentages for small datasets, top 3 categories for large ones
     - Histograms: lists values or shows range depending on dataset size

- `--alt` is silently ignored when using `-f path` (the default).

### Styling Options (all subcommands)

- `--title TEXT` — Chart title
- `--xlabel TEXT` — X-axis label
- `--ylabel TEXT` — Y-axis label
- `--width FLOAT` — Figure width in inches (default: 10)
- `--height FLOAT` — Figure height in inches (default: 6)
- `--style NAME` — Matplotlib style name (e.g. `ggplot`, `seaborn-v0_8`, `dark_background`)
- `--dpi INTEGER` — DPI for output (default: 100)

## Subcommands

### `chartroom bar`

Vertical bar chart.

```
chartroom bar [OPTIONS] [FILE]
```

- Single series: one bar per x value
- Multi-series (`-y col1 -y col2`): grouped bars side by side
- Bars are labeled with x-axis values

Example:
```bash
chartroom bar --csv --title "Sales by Region" -x region -y revenue data.csv
chartroom bar --csv -x region -y q1 -y q2 -y q3 data.csv -o grouped.png
```

### `chartroom line`

Line chart.

```
chartroom line [OPTIONS] [FILE]
```

- Single series: one line
- Multi-series (`-y col1 -y col2`): multiple overlaid lines with a legend
- Legend is shown automatically when there are multiple series

Example:
```bash
chartroom line --csv -x month -y revenue -y costs data.csv --title "Revenue vs Costs"
```

### `chartroom scatter`

Scatter plot.

```
chartroom scatter [OPTIONS] [FILE]
```

- Single series: dots at (x, y) positions
- Multi-series (`-y col1 -y col2`): different colored dot groups with a legend

Example:
```bash
chartroom scatter --json -x height -y weight people.json
```

### `chartroom pie`

Pie chart.

```
chartroom pie [OPTIONS] [FILE]
```

- `-x` selects the label column, `-y` selects the value column
- Same auto-detection rules: name/label → labels, value/count → values
- Multi-series not supported (ignores extra `-y` flags, uses first only)
- `--xlabel` and `--ylabel` are ignored for pie charts

Example:
```bash
chartroom pie --csv -x category -y amount data.csv --title "Budget Breakdown"
```

### `chartroom histogram`

Histogram (distribution of a single numeric column).

```
chartroom histogram [OPTIONS] [FILE]
```

- Only uses `-y` (the numeric column to bin). `-x` is ignored.
- `--bins INTEGER` — Number of bins (default: 10, histogram-specific option)
- If `-y` is omitted, uses auto-detection: `value`/`count` column, or second column, or first column.
- Multi-series not supported.

Example:
```bash
chartroom histogram --csv -y score results.csv --bins 20 --title "Score Distribution"
```

### `chartroom radar`

Radar (spider) chart.

```
chartroom radar [OPTIONS] [FILE]
```

- Each row is one axis/spoke of the radar. The `-x` column provides axis labels.
- Single series: one polygon
- Multi-series (`-y col1 -y col2`): overlaid polygons with a legend
- `--fill/--no-fill` — Fill radar polygons with translucent color (default: fill)
- `--xlabel` and `--ylabel` are ignored for radar charts

Example:
```bash
chartroom radar --csv -x attribute -y player1 -y player2 data.csv --title "Player Comparison"
chartroom radar --csv data.csv --no-fill -f markdown
```

## Data Type Handling

- CSV/TSV values are strings by default. The tool attempts to convert y-axis values to `float`. If conversion fails, the tool exits with an error message.
- JSON values are used as-is (numbers stay numbers).
- SQL results are used as-is.
- X-axis values are treated as categorical strings (except for scatter, where they are converted to float).

## Error Handling

- Missing required format flag → clear error message listing the three options
- Column not found → error listing available column names
- Cannot convert values to numeric → error identifying the problematic column
- SQL file not found → error
- SQL query error → error with the SQLite error message
- `--sql` combined with `--csv`/`--tsv`/`--json` → error: mutually exclusive
- `--sql` combined with FILE argument → error: mutually exclusive

## CLI Help

`chartroom --help` shows the group-level help with all subcommands listed.

Each subcommand's `--help` shows its full usage including all shared and subcommand-specific options.

## Project Structure

```
chartroom/
  __init__.py
  __main__.py
  cli.py          # Click group + subcommands
  io.py           # Data loading (CSV, TSV, JSON, SQL)
  charts.py       # Chart rendering functions
tests/
  test_chartroom.py
  test_io.py
  test_charts.py
demo/
  README.md       # showboat demo document with inline images
```

## Development

- Tests run with `uv run pytest`
- Red/green TDD: write failing test first, then implement
- Each chart type delivered incrementally with tests + demo

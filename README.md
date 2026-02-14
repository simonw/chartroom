# chartroom

[![PyPI](https://img.shields.io/pypi/v/chartroom.svg)](https://pypi.org/project/chartroom/)
[![Changelog](https://img.shields.io/github/v/release/simonw/chartroom?include_prereleases&label=changelog)](https://github.com/simonw/chartroom/releases)
[![Tests](https://github.com/simonw/chartroom/actions/workflows/test.yml/badge.svg)](https://github.com/simonw/chartroom/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/chartroom/blob/master/LICENSE)

CLI tool for creating charts from CSV, TSV, JSON, JSONL, or SQLite data using matplotlib.

## Installation

```bash
pip install chartroom
```

## Usage

```bash
chartroom --help
```

### Chart types

- `chartroom bar` - Bar chart (vertical, supports grouped bars)
- `chartroom line` - Line chart (supports multiple series)
- `chartroom scatter` - Scatter plot
- `chartroom pie` - Pie chart
- `chartroom histogram` - Histogram

### Data input

Provide data as a file, via stdin, or from a SQLite query:

```bash
# From a CSV file (auto-detected)
chartroom bar data.csv

# Explicit format
chartroom bar --csv data.csv
chartroom bar --tsv data.tsv
chartroom bar --json data.json
chartroom bar --jsonl data.jsonl

# From stdin
cat data.csv | chartroom bar --csv

# From SQLite
chartroom bar --sql mydb.sqlite "SELECT name, count FROM items"
```

### Column selection

Columns are auto-detected from common names (`name`/`label`/`x` for x-axis, `value`/`count`/`y` for y-axis), or specify explicitly:

```bash
chartroom bar --csv -x region -y revenue data.csv
```

Multiple y columns create grouped/overlaid series:

```bash
chartroom bar --csv -x region -y q1 -y q2 -y q3 data.csv
```

### Output

By default, saves to `chart.png` (incrementing to `chart-2.png` etc. to avoid overwrites). Use `-o` to specify a path:

```bash
chartroom bar --csv data.csv -o sales.png
```

The full absolute path of the output file is printed to stdout.

### Output format

Use `-f` / `--output-format` to control what is printed to stdout:

```bash
# Default: just the file path
chartroom bar --csv data.csv
# /path/to/chart.png

# Markdown image syntax
chartroom bar --csv data.csv -f markdown --alt "Sales by region"
# ![Sales by region](/path/to/chart.png)

# HTML img tag
chartroom bar --csv data.csv -f html --alt "Sales by region"
# <img src="/path/to/chart.png" alt="Sales by region">

# JSON with path and alt text
chartroom bar --csv data.csv -f json
# {"path": "/path/to/chart.png", "alt": "Bar chart of value by name — ..."}

# Just the alt text
chartroom bar --csv data.csv -f alt
# Bar chart of value by name — alice: 10, bob: 20, charlie: 15
```

When `--alt` is omitted, alt text is auto-generated from the chart title (if set) or from the chart type and data. Small datasets get all values listed; larger datasets get a summary with range and extremes.

### Alt text generation

Chartroom automatically generates descriptive alt text for every chart, making output accessible to screen readers and useful in documentation. You can use `--alt` to provide your own alt text, or let chartroom generate it from the chart type and data.

The auto-generated alt text adapts to both chart type and dataset size:

- **Bar, line, and scatter charts** — Small datasets (6 rows or fewer) list every value (e.g. `Bar chart of value by name — alice: 10, bob: 20, charlie: 15`). Larger datasets summarize the count, range, and extremes (e.g. `Bar chart of population by city. 10 points, ranging from 17118 (Dhaka) to 37400 (Tokyo)`). Multiple y-columns are noted as additional series.
- **Pie charts** — Small datasets show each category with its percentage (e.g. `Pie chart showing Rent (57%), Food (19%), Transport (10%), Other (14%)`). Larger datasets list the top 3 categories by share.
- **Histograms** — Small datasets list all values. Larger datasets describe the distribution range (e.g. `Histogram of 10 score values ranging from 76 to 95`).

If a `--title` is set, it is prepended to the generated alt text (e.g. `Team Scores. Bar chart of value by name — alice: 10, bob: 20, charlie: 15`). The `--alt` option overrides this entirely with custom text. The alt text is embedded automatically when using `-f markdown`, `-f html`, or `-f json` output formats, or can be printed on its own with `-f alt`.

See the [alt text demo](https://github.com/simonw/chartroom/blob/main/demo/alt-text.md) for worked examples of every chart type and output format.

### Styling

```bash
chartroom bar --csv data.csv --title "Sales" --xlabel "Region" --ylabel "Revenue" \
  --width 12 --height 8 --dpi 150 --style ggplot
```

## Demo

See the [live demo document](https://github.com/simonw/chartroom/blob/main/demo/README.md) for examples of every chart type, input format, and style option with inline images. The demo was built using [Showboat](https://github.com/simonw/showboat).

## Development

```bash
git clone https://github.com/simonw/chartroom
cd chartroom
uv run pytest
```

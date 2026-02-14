import json
import os
import sqlite3

from click.testing import CliRunner
from chartroom.cli import cli


def _make_csv():
    with open("data.csv", "w") as f:
        f.write("name,value\nalice,10\nbob,20\ncharlie,15\n")


# --- Default / path format ---


def test_default_format_is_path():
    """Default output (no -f) is just the absolute path."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(cli, ["bar", "--csv", "data.csv", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        output = result.output.strip()
        assert output.endswith("out.png")
        assert "![" not in output


def test_format_path_explicit():
    """-f path outputs just the path."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli, ["bar", "--csv", "data.csv", "-o", "out.png", "-f", "path"]
        )
        assert result.exit_code == 0, result.output
        output = result.output.strip()
        assert output.endswith("out.png")
        assert "![" not in output


def test_alt_ignored_with_path_format():
    """--alt is silently ignored when using default path format."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli,
            ["bar", "--csv", "data.csv", "-o", "out.png", "--alt", "Some alt text"],
        )
        assert result.exit_code == 0, result.output
        output = result.output.strip()
        assert output.endswith("out.png")
        assert "Some alt text" not in output


# --- Markdown format ---


def test_format_markdown_with_alt():
    """-f markdown --alt produces ![alt](path)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli,
            [
                "bar",
                "--csv",
                "data.csv",
                "-o",
                "out.png",
                "-f",
                "markdown",
                "--alt",
                "Sales by region",
            ],
        )
        assert result.exit_code == 0, result.output
        output = result.output.strip()
        assert output.startswith("![Sales by region](")
        assert output.endswith("out.png)")


def test_format_markdown_auto_alt_from_title():
    """-f markdown without --alt uses --title as alt text."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli,
            [
                "bar",
                "--csv",
                "data.csv",
                "-o",
                "out.png",
                "-f",
                "markdown",
                "--title",
                "Revenue Chart",
            ],
        )
        assert result.exit_code == 0, result.output
        output = result.output.strip()
        assert output.startswith("![Revenue Chart](")


def test_format_markdown_auto_alt_generated():
    """-f markdown without --alt or --title generates alt from chart type and columns."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli, ["bar", "--csv", "data.csv", "-o", "out.png", "-f", "markdown"]
        )
        assert result.exit_code == 0, result.output
        output = result.output.strip()
        assert output.startswith("![")
        assert output.endswith("out.png)")
        # Extract alt text
        alt = output.split("](")[0][2:]
        assert len(alt) > 0


def test_format_markdown_alt_overrides_title():
    """--alt takes precedence over --title for alt text."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli,
            [
                "bar",
                "--csv",
                "data.csv",
                "-o",
                "out.png",
                "-f",
                "markdown",
                "--title",
                "Title Text",
                "--alt",
                "Alt Text",
            ],
        )
        assert result.exit_code == 0, result.output
        output = result.output.strip()
        assert output.startswith("![Alt Text](")


def test_format_long_option_name():
    """--output-format works as the long form of -f."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli,
            [
                "bar",
                "--csv",
                "data.csv",
                "-o",
                "out.png",
                "--output-format",
                "markdown",
                "--alt",
                "test",
            ],
        )
        assert result.exit_code == 0, result.output
        assert result.output.strip().startswith("![test](")


# --- HTML format ---


def test_format_html_with_alt():
    """-f html produces <img> tag."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli,
            [
                "bar",
                "--csv",
                "data.csv",
                "-o",
                "out.png",
                "-f",
                "html",
                "--alt",
                "Sales chart",
            ],
        )
        assert result.exit_code == 0, result.output
        output = result.output.strip()
        assert output.startswith('<img src="')
        assert 'alt="Sales chart"' in output
        assert "out.png" in output


def test_format_html_auto_alt():
    """-f html without --alt generates alt text."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli, ["bar", "--csv", "data.csv", "-o", "out.png", "-f", "html"]
        )
        assert result.exit_code == 0, result.output
        output = result.output.strip()
        assert output.startswith('<img src="')
        assert 'alt="' in output


def test_format_html_escapes_special_chars():
    """-f html escapes special characters in alt text."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli,
            [
                "bar",
                "--csv",
                "data.csv",
                "-o",
                "out.png",
                "-f",
                "html",
                "--alt",
                'Chart with "quotes" & <tags>',
            ],
        )
        assert result.exit_code == 0, result.output
        output = result.output.strip()
        assert "&amp;" in output
        assert "&lt;" in output
        assert "&quot;" in output


# --- JSON format ---


def test_format_json():
    """-f json produces {"path": ..., "alt": ...}."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli,
            [
                "bar",
                "--csv",
                "data.csv",
                "-o",
                "out.png",
                "-f",
                "json",
                "--alt",
                "My chart",
            ],
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert data["alt"] == "My chart"
        assert data["path"].endswith("out.png")


def test_format_json_auto_alt():
    """-f json without --alt auto-generates alt."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli, ["bar", "--csv", "data.csv", "-o", "out.png", "-f", "json"]
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output.strip())
        assert "path" in data
        assert "alt" in data
        assert len(data["alt"]) > 0


# --- Alt-only format ---


def test_format_alt_with_explicit_alt():
    """-f alt outputs just the alt text string."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli,
            [
                "bar",
                "--csv",
                "data.csv",
                "-o",
                "out.png",
                "-f",
                "alt",
                "--alt",
                "My bar chart",
            ],
        )
        assert result.exit_code == 0, result.output
        assert result.output.strip() == "My bar chart"


def test_format_alt_auto_generated():
    """-f alt without --alt auto-generates alt text."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli, ["bar", "--csv", "data.csv", "-o", "out.png", "-f", "alt"]
        )
        assert result.exit_code == 0, result.output
        output = result.output.strip()
        assert len(output) > 0
        assert "out.png" not in output


# --- All chart types ---


def test_format_works_with_all_chart_types():
    """Verify -f markdown works across bar, line, pie."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        for cmd in ["bar", "line", "pie"]:
            result = runner.invoke(
                cli,
                [
                    cmd,
                    "--csv",
                    "data.csv",
                    "-o",
                    f"{cmd}.png",
                    "-f",
                    "markdown",
                    "--alt",
                    f"{cmd} chart",
                ],
            )
            assert result.exit_code == 0, f"{cmd}: {result.output}"
            output = result.output.strip()
            assert output.startswith(f"![{cmd} chart]("), f"{cmd}: {output}"


def test_format_scatter():
    """Verify -f markdown works with scatter."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("x,y\n1,2\n3,4\n5,6\n")
        result = runner.invoke(
            cli,
            [
                "scatter",
                "--csv",
                "data.csv",
                "-o",
                "out.png",
                "-f",
                "markdown",
                "--alt",
                "scatter plot",
            ],
        )
        assert result.exit_code == 0, result.output
        assert result.output.strip().startswith("![scatter plot](")


def test_format_histogram():
    """Verify -f markdown works with histogram."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("value\n1\n2\n3\n4\n5\n")
        result = runner.invoke(
            cli,
            [
                "histogram",
                "--csv",
                "-y",
                "value",
                "data.csv",
                "-o",
                "out.png",
                "-f",
                "markdown",
                "--alt",
                "value distribution",
            ],
        )
        assert result.exit_code == 0, result.output
        assert result.output.strip().startswith("![value distribution](")


# --- Smart auto-generated alt text ---


def test_auto_alt_bar_small_dataset():
    """Auto-generated alt for bar with few items lists all values."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli, ["bar", "--csv", "data.csv", "-o", "out.png", "-f", "alt"]
        )
        assert result.exit_code == 0, result.output
        alt = result.output.strip()
        assert "Bar chart" in alt
        assert "alice" in alt
        assert "bob" in alt
        assert "charlie" in alt


def test_auto_alt_bar_large_dataset():
    """Auto-generated alt for bar with many items summarizes instead of listing all."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\n")
            for i in range(20):
                f.write(f"item{i},{i * 10}\n")
        result = runner.invoke(
            cli, ["bar", "--csv", "data.csv", "-o", "out.png", "-f", "alt"]
        )
        assert result.exit_code == 0, result.output
        alt = result.output.strip()
        assert "Bar chart" in alt
        assert "20 points" in alt
        # Should mention range, not list every item
        assert "ranging from" in alt


def test_auto_alt_line_chart():
    """Auto-generated alt text for line chart includes chart type."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("month,revenue\nJan,100\nFeb,120\n")
        result = runner.invoke(
            cli, ["line", "--csv", "data.csv", "-o", "out.png", "-f", "alt"]
        )
        assert result.exit_code == 0, result.output
        alt = result.output.strip().lower()
        assert "line" in alt


def test_auto_alt_pie_chart_small():
    """Auto-generated alt text for pie chart with few slices shows percentages."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli, ["pie", "--csv", "data.csv", "-o", "out.png", "-f", "alt"]
        )
        assert result.exit_code == 0, result.output
        alt = result.output.strip()
        assert "Pie chart" in alt
        assert "%" in alt


def test_auto_alt_pie_chart_large():
    """Auto-generated alt for pie with many slices summarizes top categories."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\n")
            for i in range(10):
                f.write(f"cat{i},{(10 - i) * 5}\n")
        result = runner.invoke(
            cli, ["pie", "--csv", "data.csv", "-o", "out.png", "-f", "alt"]
        )
        assert result.exit_code == 0, result.output
        alt = result.output.strip()
        assert "Pie chart" in alt
        assert "Largest" in alt


def test_auto_alt_histogram():
    """Auto-generated alt text for histogram describes the distribution."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("score\n")
            for s in [85, 90, 78, 92, 88, 76, 95, 82, 89, 91]:
                f.write(f"{s}\n")
        result = runner.invoke(
            cli,
            [
                "histogram",
                "--csv",
                "-y",
                "score",
                "data.csv",
                "-o",
                "out.png",
                "-f",
                "alt",
            ],
        )
        assert result.exit_code == 0, result.output
        alt = result.output.strip()
        assert "Histogram" in alt
        assert "score" in alt
        assert "ranging from" in alt


def test_auto_alt_histogram_small():
    """Auto-generated alt for histogram with few values lists them all."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("value\n10\n20\n30\n")
        result = runner.invoke(
            cli,
            [
                "histogram",
                "--csv",
                "-y",
                "value",
                "data.csv",
                "-o",
                "out.png",
                "-f",
                "alt",
            ],
        )
        assert result.exit_code == 0, result.output
        alt = result.output.strip()
        assert "Histogram" in alt
        assert "10" in alt
        assert "20" in alt
        assert "30" in alt


def test_auto_alt_scatter():
    """Auto-generated alt for scatter plot describes the data."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("x,y\n1,10\n2,20\n3,15\n")
        result = runner.invoke(
            cli, ["scatter", "--csv", "data.csv", "-o", "out.png", "-f", "alt"]
        )
        assert result.exit_code == 0, result.output
        alt = result.output.strip()
        assert "Scatter plot" in alt


def test_auto_alt_multi_series():
    """Auto-generated alt for multi-series chart mentions additional series."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,q1,q2\nalice,10,15\nbob,20,25\n")
        result = runner.invoke(
            cli,
            [
                "bar",
                "--csv",
                "-x",
                "name",
                "-y",
                "q1",
                "-y",
                "q2",
                "data.csv",
                "-o",
                "out.png",
                "-f",
                "alt",
            ],
        )
        assert result.exit_code == 0, result.output
        alt = result.output.strip()
        assert "1 more series" in alt


def test_auto_alt_uses_title_when_provided():
    """When --title is given, auto-generated alt text uses the title."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        result = runner.invoke(
            cli,
            [
                "bar",
                "--csv",
                "data.csv",
                "-o",
                "out.png",
                "-f",
                "alt",
                "--title",
                "My Custom Title",
            ],
        )
        assert result.exit_code == 0, result.output
        assert result.output.strip() == "My Custom Title"

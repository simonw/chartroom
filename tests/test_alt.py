import json
import os

from click.testing import CliRunner
from inline_snapshot import snapshot

from chartroom.cli import cli


def _make_csv():
    with open("data.csv", "w") as f:
        f.write("name,value\nalice,10\nbob,20\ncharlie,15\n")


def _get_alt(args):
    """Run chartroom with -f alt and return the alt text."""
    runner = CliRunner()
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.output
    return result.output.strip()


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
        assert output.startswith("![Revenue Chart. ")


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


# --- All chart types with explicit --alt ---


def test_format_works_with_all_chart_types():
    """Verify -f markdown works across bar, line, pie, radar."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        for cmd in ["bar", "line", "pie", "radar"]:
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


# --- Smart auto-generated alt text (inline snapshots) ---


def test_auto_alt_bar_small():
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        alt = _get_alt(["bar", "--csv", "data.csv", "-o", "out.png", "-f", "alt"])
        assert alt == snapshot(
            "Bar chart of value by name — alice: 10, bob: 20, charlie: 15"
        )


def test_auto_alt_bar_large():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\n")
            for i in range(20):
                f.write(f"item{i},{i * 10}\n")
        alt = _get_alt(["bar", "--csv", "data.csv", "-o", "out.png", "-f", "alt"])
        assert alt == snapshot(
            "Bar chart of value by name. 20 points, ranging from 0 (item0) to 190 (item19)"
        )


def test_auto_alt_bar_with_title():
    runner = CliRunner()
    with runner.isolated_filesystem():
        _make_csv()
        alt = _get_alt(
            [
                "bar",
                "--csv",
                "data.csv",
                "-o",
                "out.png",
                "-f",
                "alt",
                "--title",
                "Team Scores",
            ]
        )
        assert alt == snapshot('Team Scores. Bar chart of value by name — alice: 10, bob: 20, charlie: 15')


def test_auto_alt_line_small():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("month,revenue\nJan,100\nFeb,120\nMar,115\nApr,140\n")
        alt = _get_alt(["line", "--csv", "data.csv", "-o", "out.png", "-f", "alt"])
        assert alt == snapshot(
            "Line chart of revenue by month — Jan: 100, Feb: 120, Mar: 115, Apr: 140"
        )


def test_auto_alt_line_large():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("day,temp\n")
            for i in range(30):
                f.write(f"day{i},{15 + (i % 7) * 3}\n")
        alt = _get_alt(["line", "--csv", "data.csv", "-o", "out.png", "-f", "alt"])
        assert alt == snapshot(
            "Line chart of temp by day. 30 points, ranging from 15 (day0) to 33 (day6)"
        )


def test_auto_alt_scatter():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("x,y\n1,10\n2,20\n3,15\n4,25\n5,18\n")
        alt = _get_alt(["scatter", "--csv", "data.csv", "-o", "out.png", "-f", "alt"])
        assert alt == snapshot(
            "Scatter plot of y by x — 1: 10, 2: 20, 3: 15, 4: 25, 5: 18"
        )


def test_auto_alt_pie_small():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\nRent,1200\nFood,400\nTransport,200\nOther,300\n")
        alt = _get_alt(["pie", "--csv", "data.csv", "-o", "out.png", "-f", "alt"])
        assert alt == snapshot(
            "Pie chart showing Rent (57%), Food (19%), Transport (10%), Other (14%)"
        )


def test_auto_alt_pie_large():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\n")
            for i in range(10):
                f.write(f"cat{i},{(10 - i) * 5}\n")
        alt = _get_alt(["pie", "--csv", "data.csv", "-o", "out.png", "-f", "alt"])
        assert alt == snapshot(
            "Pie chart of 10 categories. Largest: cat0 (18%), cat1 (16%), cat2 (15%)"
        )


def test_auto_alt_histogram_small():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("value\n10\n20\n30\n")
        alt = _get_alt(
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
            ]
        )
        assert alt == snapshot("Histogram of value values: 10, 20, 30")


def test_auto_alt_histogram_large():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("score\n")
            for s in [85, 90, 78, 92, 88, 76, 95, 82, 89, 91]:
                f.write(f"{s}\n")
        alt = _get_alt(
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
            ]
        )
        assert alt == snapshot("Histogram of 10 score values ranging from 76 to 95")


def test_auto_alt_multi_series():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,q1,q2\nalice,10,15\nbob,20,25\n")
        alt = _get_alt(
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
            ]
        )
        assert alt == snapshot(
            "Bar chart of q1 by name — alice: 10, bob: 20 and 1 more series"
        )


def test_auto_alt_radar_small():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\nSpeed,9\nPower,5\nDefense,7\nAccuracy,8\nStamina,6\n")
        alt = _get_alt(["radar", "--csv", "data.csv", "-o", "out.png", "-f", "alt"])
        assert alt == snapshot(
            "Radar chart of value by name — Speed: 9, Power: 5, Defense: 7, Accuracy: 8, Stamina: 6"
        )


def test_auto_alt_radar_multi_series():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write(
                "attribute,player1,player2\n"
                "Speed,9,7\nPower,5,8\nDefense,7,6\n"
            )
        alt = _get_alt(
            [
                "radar",
                "--csv",
                "-x",
                "attribute",
                "-y",
                "player1",
                "-y",
                "player2",
                "data.csv",
                "-o",
                "out.png",
                "-f",
                "alt",
            ]
        )
        assert alt == snapshot(
            "Radar chart of player1 by attribute — Speed: 9, Power: 5, Defense: 7 and 1 more series"
        )


def test_format_radar():
    """Verify -f markdown works with radar."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\nSpeed,9\nPower,5\nDefense,7\n")
        result = runner.invoke(
            cli,
            [
                "radar",
                "--csv",
                "data.csv",
                "-o",
                "out.png",
                "-f",
                "markdown",
                "--alt",
                "radar chart",
            ],
        )
        assert result.exit_code == 0, result.output
        assert result.output.strip().startswith("![radar chart](")

import os
import sqlite3
import tempfile

from click.testing import CliRunner
from chartroom.cli import cli


def test_version():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output


def test_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "bar" in result.output
    assert "line" in result.output
    assert "scatter" in result.output
    assert "pie" in result.output
    assert "histogram" in result.output


def test_bar_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["bar", "--help"])
    assert result.exit_code == 0
    assert "--csv" in result.output
    assert "--sql" in result.output
    assert "--title" in result.output
    assert "-o" in result.output


def test_styles():
    runner = CliRunner()
    result = runner.invoke(cli, ["styles"])
    assert result.exit_code == 0
    assert "ggplot" in result.output
    assert "dark_background" in result.output
    for line in result.output.strip().split("\n"):
        assert not line.startswith("_")


# --- Bar chart ---


def test_bar_csv_file():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\nalice,10\nbob,20\ncharlie,15\n")
        result = runner.invoke(cli, ["bar", "--csv", "data.csv", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        assert result.output.strip().endswith("out.png")
        assert os.path.exists("out.png")
        assert os.path.getsize("out.png") > 0


def test_bar_csv_stdin():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["bar", "--csv", "-o", "out.png"],
            input="name,value\nalice,10\nbob,20\n",
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_bar_tsv():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.tsv", "w") as f:
            f.write("name\tvalue\nalice\t10\nbob\t20\n")
        result = runner.invoke(cli, ["bar", "--tsv", "data.tsv", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_bar_json():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.json", "w") as f:
            f.write('[{"name": "alice", "value": 10}, {"name": "bob", "value": 20}]')
        result = runner.invoke(cli, ["bar", "--json", "data.json", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_bar_jsonl():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.jsonl", "w") as f:
            f.write('{"name": "alice", "value": 10}\n{"name": "bob", "value": 20}\n')
        result = runner.invoke(cli, ["bar", "--jsonl", "data.jsonl", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_bar_auto_detect_csv():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\nalice,10\nbob,20\n")
        result = runner.invoke(cli, ["bar", "data.csv", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_bar_auto_detect_json():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.json", "w") as f:
            f.write('[{"name": "alice", "value": 10}]')
        result = runner.invoke(cli, ["bar", "data.json", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_bar_sql():
    runner = CliRunner()
    with runner.isolated_filesystem():
        conn = sqlite3.connect("test.db")
        conn.execute("CREATE TABLE t (name TEXT, value INTEGER)")
        conn.execute("INSERT INTO t VALUES ('alice', 10)")
        conn.execute("INSERT INTO t VALUES ('bob', 20)")
        conn.commit()
        conn.close()
        result = runner.invoke(
            cli, ["bar", "--sql", "test.db", "SELECT * FROM t", "-o", "out.png"]
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_bar_explicit_columns():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("a,b,c\nalice,10,99\nbob,20,88\n")
        result = runner.invoke(
            cli, ["bar", "--csv", "-x", "a", "-y", "b", "data.csv", "-o", "out.png"]
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_bar_multi_y():
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
            ],
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_bar_styling():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\nalice,10\nbob,20\n")
        result = runner.invoke(
            cli,
            [
                "bar",
                "--csv",
                "data.csv",
                "-o",
                "out.png",
                "--title",
                "My Chart",
                "--xlabel",
                "Name",
                "--ylabel",
                "Value",
                "--width",
                "12",
                "--height",
                "8",
                "--dpi",
                "150",
            ],
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


# --- Output path handling ---


def test_auto_output_filename():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\nalice,10\n")
        result = runner.invoke(cli, ["bar", "--csv", "data.csv"])
        assert result.exit_code == 0, result.output
        output_path = result.output.strip()
        assert output_path.endswith("chart.png")
        assert os.path.exists("chart.png")


def test_auto_output_increments():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\nalice,10\n")
        # Create chart.png first
        open("chart.png", "w").close()
        result = runner.invoke(cli, ["bar", "--csv", "data.csv"])
        assert result.exit_code == 0, result.output
        output_path = result.output.strip()
        assert output_path.endswith("chart-2.png")


def test_output_is_absolute_path():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\nalice,10\n")
        result = runner.invoke(cli, ["bar", "--csv", "data.csv", "-o", "out.png"])
        output_path = result.output.strip()
        assert os.path.isabs(output_path)


# --- Error handling ---


def test_no_input():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["bar", "-o", "out.png"])
        assert result.exit_code != 0
        assert "Provide a FILE argument" in result.output or "Error" in result.output


def test_sql_with_csv_flag():
    runner = CliRunner()
    with runner.isolated_filesystem():
        conn = sqlite3.connect("test.db")
        conn.execute("CREATE TABLE t (name TEXT)")
        conn.commit()
        conn.close()
        result = runner.invoke(
            cli, ["bar", "--sql", "test.db", "SELECT * FROM t", "--csv"]
        )
        assert result.exit_code != 0


def test_missing_column():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\nalice,10\n")
        result = runner.invoke(
            cli, ["bar", "--csv", "-x", "missing", "data.csv", "-o", "out.png"]
        )
        assert result.exit_code != 0


# --- Line chart ---


def test_line_csv():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("month,revenue\nJan,100\nFeb,120\nMar,115\nApr,140\n")
        result = runner.invoke(cli, ["line", "--csv", "data.csv", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")
        assert os.path.getsize("out.png") > 0


def test_line_multi_series():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("month,revenue,costs\nJan,100,80\nFeb,120,90\nMar,115,85\n")
        result = runner.invoke(
            cli,
            [
                "line",
                "--csv",
                "-x",
                "month",
                "-y",
                "revenue",
                "-y",
                "costs",
                "data.csv",
                "-o",
                "out.png",
                "--title",
                "Revenue vs Costs",
            ],
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_line_json():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.json", "w") as f:
            f.write('[{"month": "Jan", "value": 100}, {"month": "Feb", "value": 120}]')
        result = runner.invoke(cli, ["line", "--json", "data.json", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_line_sql():
    runner = CliRunner()
    with runner.isolated_filesystem():
        conn = sqlite3.connect("test.db")
        conn.execute("CREATE TABLE t (month TEXT, value INTEGER)")
        conn.execute("INSERT INTO t VALUES ('Jan', 100)")
        conn.execute("INSERT INTO t VALUES ('Feb', 120)")
        conn.commit()
        conn.close()
        result = runner.invoke(
            cli, ["line", "--sql", "test.db", "SELECT * FROM t", "-o", "out.png"]
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_line_stdin():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ["line", "--csv", "-o", "out.png"], input="x,y\n1,10\n2,20\n3,15\n"
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


# --- Scatter chart ---


def test_scatter_csv():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("x,y\n1,2\n3,4\n5,3\n7,8\n")
        result = runner.invoke(cli, ["scatter", "--csv", "data.csv", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")
        assert os.path.getsize("out.png") > 0


def test_scatter_explicit_columns():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("height,weight,age\n170,65,30\n180,80,25\n165,55,35\n")
        result = runner.invoke(
            cli,
            [
                "scatter",
                "--csv",
                "-x",
                "height",
                "-y",
                "weight",
                "data.csv",
                "-o",
                "out.png",
            ],
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_scatter_multi_y():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("x,y1,y2\n1,2,3\n3,4,1\n5,3,5\n")
        result = runner.invoke(
            cli,
            [
                "scatter",
                "--csv",
                "-x",
                "x",
                "-y",
                "y1",
                "-y",
                "y2",
                "data.csv",
                "-o",
                "out.png",
            ],
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_scatter_json():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.json", "w") as f:
            f.write('[{"x": 1, "y": 2}, {"x": 3, "y": 4}, {"x": 5, "y": 3}]')
        result = runner.invoke(cli, ["scatter", "--json", "data.json", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_scatter_sql():
    runner = CliRunner()
    with runner.isolated_filesystem():
        conn = sqlite3.connect("test.db")
        conn.execute("CREATE TABLE t (x REAL, y REAL)")
        conn.execute("INSERT INTO t VALUES (1.0, 2.0)")
        conn.execute("INSERT INTO t VALUES (3.0, 4.0)")
        conn.commit()
        conn.close()
        result = runner.invoke(
            cli, ["scatter", "--sql", "test.db", "SELECT * FROM t", "-o", "out.png"]
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


# --- Pie chart ---


def test_pie_csv():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\nRent,1200\nFood,400\nTransport,200\nOther,300\n")
        result = runner.invoke(cli, ["pie", "--csv", "data.csv", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")
        assert os.path.getsize("out.png") > 0


def test_pie_with_title():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("label,count\nA,10\nB,20\nC,30\n")
        result = runner.invoke(
            cli,
            ["pie", "--csv", "data.csv", "-o", "out.png", "--title", "Distribution"],
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_pie_json():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.json", "w") as f:
            f.write('[{"name": "A", "value": 10}, {"name": "B", "value": 20}]')
        result = runner.invoke(cli, ["pie", "--json", "data.json", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_pie_sql():
    runner = CliRunner()
    with runner.isolated_filesystem():
        conn = sqlite3.connect("test.db")
        conn.execute("CREATE TABLE t (name TEXT, value INTEGER)")
        conn.execute("INSERT INTO t VALUES ('A', 10)")
        conn.execute("INSERT INTO t VALUES ('B', 20)")
        conn.commit()
        conn.close()
        result = runner.invoke(
            cli, ["pie", "--sql", "test.db", "SELECT * FROM t", "-o", "out.png"]
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


# --- Histogram ---


def test_histogram_csv():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("score\n85\n90\n78\n92\n88\n76\n95\n82\n89\n91\n")
        result = runner.invoke(
            cli, ["histogram", "--csv", "-y", "score", "data.csv", "-o", "out.png"]
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")
        assert os.path.getsize("out.png") > 0


def test_histogram_bins():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("value\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n")
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
                "--bins",
                "5",
            ],
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_histogram_auto_column():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\na,85\nb,90\nc,78\nd,92\ne,88\n")
        result = runner.invoke(cli, ["histogram", "--csv", "data.csv", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_histogram_json():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.json", "w") as f:
            f.write('[{"value": 10}, {"value": 20}, {"value": 15}, {"value": 25}]')
        result = runner.invoke(
            cli, ["histogram", "--json", "data.json", "-o", "out.png"]
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_histogram_sql():
    runner = CliRunner()
    with runner.isolated_filesystem():
        conn = sqlite3.connect("test.db")
        conn.execute("CREATE TABLE t (value REAL)")
        for v in [10, 20, 15, 25, 30, 12, 18]:
            conn.execute("INSERT INTO t VALUES (?)", (v,))
        conn.commit()
        conn.close()
        result = runner.invoke(
            cli, ["histogram", "--sql", "test.db", "SELECT * FROM t", "-o", "out.png"]
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_histogram_with_title():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("score\n85\n90\n78\n92\n88\n")
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
                "--title",
                "Score Distribution",
                "--xlabel",
                "Score",
                "--ylabel",
                "Frequency",
            ],
        )
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")

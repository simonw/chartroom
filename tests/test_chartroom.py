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
            cli, ["bar", "--csv", "-o", "out.png"],
            input="name,value\nalice,10\nbob,20\n"
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
        result = runner.invoke(cli, ["bar", "--sql", "test.db", "SELECT * FROM t", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_bar_explicit_columns():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("a,b,c\nalice,10,99\nbob,20,88\n")
        result = runner.invoke(cli, ["bar", "--csv", "-x", "a", "-y", "b", "data.csv", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_bar_multi_y():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,q1,q2\nalice,10,15\nbob,20,25\n")
        result = runner.invoke(cli, ["bar", "--csv", "-x", "name", "-y", "q1", "-y", "q2", "data.csv", "-o", "out.png"])
        assert result.exit_code == 0, result.output
        assert os.path.exists("out.png")


def test_bar_styling():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\nalice,10\nbob,20\n")
        result = runner.invoke(cli, [
            "bar", "--csv", "data.csv", "-o", "out.png",
            "--title", "My Chart", "--xlabel", "Name", "--ylabel", "Value",
            "--width", "12", "--height", "8", "--dpi", "150",
        ])
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
        result = runner.invoke(cli, ["bar", "--sql", "test.db", "SELECT * FROM t", "--csv"])
        assert result.exit_code != 0


def test_missing_column():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("data.csv", "w") as f:
            f.write("name,value\nalice,10\n")
        result = runner.invoke(cli, ["bar", "--csv", "-x", "missing", "data.csv", "-o", "out.png"])
        assert result.exit_code != 0

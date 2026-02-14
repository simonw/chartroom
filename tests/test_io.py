import io
import json
import os
import sqlite3
import tempfile

import pytest

from chartroom.io import (
    load_rows,
    load_rows_from_csv,
    load_rows_from_tsv,
    load_rows_from_json,
    load_rows_from_jsonl,
    load_rows_from_sql,
    detect_format,
    resolve_columns,
)


# --- CSV ---

def test_load_csv():
    data = b"name,value\nalice,10\nbob,20\n"
    rows = load_rows_from_csv(io.BytesIO(data))
    assert rows == [{"name": "alice", "value": "10"}, {"name": "bob", "value": "20"}]


def test_load_csv_utf8_bom():
    data = b"\xef\xbb\xbfname,value\nalice,10\n"
    rows = load_rows_from_csv(io.BytesIO(data))
    assert rows == [{"name": "alice", "value": "10"}]


# --- TSV ---

def test_load_tsv():
    data = b"name\tvalue\nalice\t10\nbob\t20\n"
    rows = load_rows_from_tsv(io.BytesIO(data))
    assert rows == [{"name": "alice", "value": "10"}, {"name": "bob", "value": "20"}]


# --- JSON ---

def test_load_json_array():
    data = json.dumps([{"name": "alice", "value": 10}]).encode()
    rows = load_rows_from_json(io.BytesIO(data))
    assert rows == [{"name": "alice", "value": 10}]


def test_load_json_single_object():
    data = json.dumps({"name": "alice", "value": 10}).encode()
    rows = load_rows_from_json(io.BytesIO(data))
    assert rows == [{"name": "alice", "value": 10}]


def test_load_json_bad_format():
    data = b'"just a string"'
    with pytest.raises(ValueError, match="JSON must be a list or a dictionary"):
        load_rows_from_json(io.BytesIO(data))


# --- JSONL ---

def test_load_jsonl():
    data = b'{"name": "alice", "value": 10}\n{"name": "bob", "value": 20}\n'
    rows = load_rows_from_jsonl(io.BytesIO(data))
    assert rows == [
        {"name": "alice", "value": 10},
        {"name": "bob", "value": 20},
    ]


def test_load_jsonl_blank_lines():
    data = b'{"name": "alice"}\n\n{"name": "bob"}\n'
    rows = load_rows_from_jsonl(io.BytesIO(data))
    assert rows == [{"name": "alice"}, {"name": "bob"}]


# --- SQL ---

def test_load_sql():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE t (name TEXT, value INTEGER)")
        conn.execute("INSERT INTO t VALUES ('alice', 10)")
        conn.execute("INSERT INTO t VALUES ('bob', 20)")
        conn.commit()
        conn.close()

        rows = load_rows_from_sql(db_path, "SELECT name, value FROM t ORDER BY name")
        assert rows == [{"name": "alice", "value": 10}, {"name": "bob", "value": 20}]
    finally:
        os.unlink(db_path)


def test_load_sql_read_only():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE t (name TEXT)")
        conn.commit()
        conn.close()

        with pytest.raises(sqlite3.OperationalError):
            load_rows_from_sql(db_path, "INSERT INTO t VALUES ('hack')")
    finally:
        os.unlink(db_path)


# --- Auto-detection ---

def test_detect_csv():
    data = b"name,value\nalice,10\nbob,20\n"
    fmt, fp = detect_format(io.BytesIO(data))
    assert fmt == "csv"


def test_detect_tsv():
    data = b"name\tvalue\nalice\t10\nbob\t20\n"
    fmt, fp = detect_format(io.BytesIO(data))
    assert fmt == "tsv"


def test_detect_json():
    data = json.dumps([{"name": "alice"}]).encode()
    fmt, fp = detect_format(io.BytesIO(data))
    assert fmt == "json"


def test_detect_jsonl():
    data = b'{"name": "alice"}\n{"name": "bob"}\n'
    fmt, fp = detect_format(io.BytesIO(data))
    assert fmt == "jsonl"


def test_load_rows_auto_csv():
    data = b"name,value\nalice,10\n"
    rows = load_rows(io.BytesIO(data))
    assert rows == [{"name": "alice", "value": "10"}]


def test_load_rows_auto_json():
    data = json.dumps([{"name": "alice", "value": 10}]).encode()
    rows = load_rows(io.BytesIO(data))
    assert rows == [{"name": "alice", "value": 10}]


def test_load_rows_explicit_format():
    data = b"name,value\nalice,10\n"
    rows = load_rows(io.BytesIO(data), format="csv")
    assert rows == [{"name": "alice", "value": "10"}]


def test_load_rows_sql_mode():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE t (name TEXT, value INTEGER)")
        conn.execute("INSERT INTO t VALUES ('alice', 10)")
        conn.commit()
        conn.close()

        rows = load_rows(sql_db=db_path, sql_query="SELECT * FROM t")
        assert rows == [{"name": "alice", "value": 10}]
    finally:
        os.unlink(db_path)


# --- Column resolution ---

def test_resolve_columns_explicit():
    rows = [{"a": 1, "b": 2, "c": 3}]
    x, y = resolve_columns(rows, x="a", y=("b",))
    assert x == "a"
    assert y == ["b"]


def test_resolve_columns_auto_name_value():
    rows = [{"name": "alice", "value": 10, "extra": "x"}]
    x, y = resolve_columns(rows, x=None, y=())
    assert x == "name"
    assert y == ["value"]


def test_resolve_columns_auto_label_count():
    rows = [{"label": "a", "count": 5}]
    x, y = resolve_columns(rows, x=None, y=())
    assert x == "label"
    assert y == ["count"]


def test_resolve_columns_auto_x_y():
    rows = [{"x": 1, "y": 2}]
    x, ys = resolve_columns(rows, x=None, y=())
    assert x == "x"
    assert ys == ["y"]


def test_resolve_columns_fallback_first_second():
    rows = [{"foo": "a", "bar": 10}]
    x, y = resolve_columns(rows, x=None, y=())
    assert x == "foo"
    assert y == ["bar"]


def test_resolve_columns_scatter_prefers_x_y():
    rows = [{"x": 1, "y": 2, "name": "a"}]
    x, ys = resolve_columns(rows, x=None, y=(), chart_type="scatter")
    assert x == "x"
    assert ys == ["y"]


def test_resolve_columns_histogram():
    rows = [{"score": 95, "value": 10}]
    x, y = resolve_columns(rows, x=None, y=(), chart_type="histogram")
    assert x is None
    assert y == ["value"]


def test_resolve_columns_missing_column():
    rows = [{"a": 1, "b": 2}]
    with pytest.raises(ValueError, match="Column 'z' not found"):
        resolve_columns(rows, x="z", y=())


def test_resolve_columns_empty():
    with pytest.raises(ValueError, match="No data rows"):
        resolve_columns([], x=None, y=())


def test_resolve_columns_multi_y():
    rows = [{"x": 1, "a": 2, "b": 3}]
    x, ys = resolve_columns(rows, x="x", y=("a", "b"))
    assert ys == ["a", "b"]

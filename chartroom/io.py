import csv
import io
import json
import sqlite3
from typing import List, Dict, Any, Optional, BinaryIO, Tuple


def load_rows_from_sql(db_path: str, query: str) -> List[Dict[str, Any]]:
    """Execute a SQL query against a SQLite database in read-only mode."""
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def load_rows_from_csv(fp: BinaryIO, encoding: str = "utf-8-sig") -> List[Dict[str, Any]]:
    """Parse CSV from a binary file-like object."""
    text = io.TextIOWrapper(fp, encoding=encoding)
    reader = csv.DictReader(text)
    return [dict(row) for row in reader]


def load_rows_from_tsv(fp: BinaryIO, encoding: str = "utf-8-sig") -> List[Dict[str, Any]]:
    """Parse TSV from a binary file-like object."""
    text = io.TextIOWrapper(fp, encoding=encoding)
    reader = csv.DictReader(text, dialect=csv.excel_tab)
    return [dict(row) for row in reader]


def load_rows_from_json(fp: BinaryIO) -> List[Dict[str, Any]]:
    """Parse JSON array of objects from a binary file-like object."""
    decoded = json.load(fp)
    if isinstance(decoded, dict):
        decoded = [decoded]
    if not isinstance(decoded, list):
        raise ValueError("JSON must be a list or a dictionary")
    return decoded


def load_rows_from_jsonl(fp: BinaryIO) -> List[Dict[str, Any]]:
    """Parse newline-delimited JSON from a binary file-like object."""
    return [json.loads(line) for line in fp if line.strip()]


def detect_format(fp: BinaryIO) -> Tuple[str, BinaryIO]:
    """Detect file format by peeking at content. Returns (format_name, buffered_fp)."""
    buffered = io.BufferedReader(fp, buffer_size=4096)
    first_bytes = buffered.peek(2048).strip()
    if first_bytes.startswith(b"[") or first_bytes.startswith(b"{"):
        # Could be JSON or JSONL - check if first line is a complete object
        # followed by more lines
        lines = first_bytes.split(b"\n", 2)
        if len(lines) >= 2 and lines[0].strip().startswith(b"{") and not first_bytes.startswith(b"["):
            return "jsonl", buffered
        return "json", buffered
    else:
        # Try to detect CSV vs TSV
        try:
            dialect = csv.Sniffer().sniff(first_bytes.decode("utf-8-sig", "ignore"))
            if dialect.delimiter == "\t":
                return "tsv", buffered
        except csv.Error:
            pass
        return "csv", buffered


def load_rows(
    fp: Optional[BinaryIO] = None,
    format: Optional[str] = None,
    sql_db: Optional[str] = None,
    sql_query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Load rows from the given source.

    Either provide fp (with optional format) or sql_db + sql_query.
    Format can be: csv, tsv, json, jsonl, or None for auto-detect.
    """
    if sql_db is not None:
        if sql_query is None:
            raise ValueError("--sql requires both a database path and a query")
        return load_rows_from_sql(sql_db, sql_query)

    if fp is None:
        raise ValueError("No input provided")

    if format is None:
        format, fp = detect_format(fp)

    loaders = {
        "csv": load_rows_from_csv,
        "tsv": load_rows_from_tsv,
        "json": load_rows_from_json,
        "jsonl": load_rows_from_jsonl,
    }
    loader = loaders.get(format)
    if loader is None:
        raise ValueError(f"Unknown format: {format}")
    return loader(fp)


def resolve_columns(
    rows: List[Dict[str, Any]],
    x: Optional[str],
    y: Optional[Tuple[str, ...]],
    chart_type: str = "bar",
) -> Tuple[str, List[str]]:
    """
    Resolve x and y column names from explicit values or auto-detection.

    Returns (x_col, [y_cols]).
    """
    if not rows:
        raise ValueError("No data rows found")

    columns = list(rows[0].keys())

    x_col = x
    y_cols = list(y) if y else []

    # Auto-detect x column
    if x_col is None:
        if chart_type == "histogram":
            x_col = None  # histogram doesn't use x
        elif chart_type == "scatter":
            # For scatter, prefer 'x' column name
            for candidate in ("x", "name", "label"):
                if candidate in columns:
                    x_col = candidate
                    break
            if x_col is None:
                x_col = columns[0]
        else:
            for candidate in ("name", "label", "x"):
                if candidate in columns:
                    x_col = candidate
                    break
            if x_col is None:
                x_col = columns[0]

    # Auto-detect y column(s)
    if not y_cols:
        if chart_type == "histogram":
            # For histogram, prefer value/count/y, or first numeric-looking column
            for candidate in ("value", "count", "y"):
                if candidate in columns:
                    y_cols = [candidate]
                    break
            if not y_cols:
                # Use second column if available, else first
                if len(columns) > 1:
                    y_cols = [columns[1]]
                else:
                    y_cols = [columns[0]]
        elif chart_type == "scatter":
            for candidate in ("y", "value", "count"):
                if candidate in columns:
                    y_cols = [candidate]
                    break
            if not y_cols:
                if len(columns) > 1:
                    y_cols = [columns[1]]
                else:
                    raise ValueError("Scatter chart requires at least two columns")
        else:
            for candidate in ("value", "count", "y"):
                if candidate in columns:
                    y_cols = [candidate]
                    break
            if not y_cols:
                if len(columns) > 1:
                    y_cols = [columns[1]]
                else:
                    raise ValueError("Need at least two columns for this chart type")

    # Validate columns exist
    if x_col is not None and x_col not in columns:
        raise ValueError(f"Column '{x_col}' not found. Available columns: {', '.join(columns)}")
    for yc in y_cols:
        if yc not in columns:
            raise ValueError(f"Column '{yc}' not found. Available columns: {', '.join(columns)}")

    return x_col, y_cols

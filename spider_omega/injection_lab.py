"""Safe SQL-injection source audit and local SQLite export.

The auditor inspects source files for risky query construction patterns.
The exporter reads only a user-selected local SQLite database.
"""
import ast
import csv
import json
import sqlite3
from pathlib import Path

SOURCE_SUFFIXES = {".py"}
RISK_MARKERS = (
    "execute(", "executemany(", "format(", "f-string", "%",
)

class QueryRiskVisitor(ast.NodeVisitor):
    def __init__(self):
        self.findings = []

    def visit_Call(self, node):
        name = ""
        if isinstance(node.func, ast.Attribute):
            name = node.func.attr.lower()
        elif isinstance(node.func, ast.Name):
            name = node.func.id.lower()
        if name in ("execute", "executemany"):
            if node.args:
                query = node.args[0]
                dynamic = isinstance(query, ast.JoinedStr)
                dynamic = dynamic or (
                    isinstance(query, ast.BinOp) and isinstance(query.op, (ast.Add, ast.Mod))
                )
                dynamic = dynamic or (
                    isinstance(query, ast.Call) and isinstance(query.func, ast.Attribute)
                    and query.func.attr in ("format", "format_map")
                )
                if dynamic:
                    self.findings.append({
                        "line": getattr(node, "lineno", 0),
                        "severity": "high",
                        "rule": "DYNAMIC_SQL_QUERY",
                        "detail": "SQL execution appears to build its query dynamically; use parameterized placeholders."
                    })
        self.generic_visit(node)

def audit_source_tree(root="."):
    base = Path(root).resolve()
    findings = []
    scanned = 0
    for path in base.rglob("*.py"):
        if any(part in {".git", ".venv", "venv", "__pycache__"} for part in path.parts):
            continue
        scanned += 1
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as exc:
            findings.append({"file": str(path.relative_to(base)), "severity": "info",
                             "rule": "SOURCE_SKIPPED", "detail": str(exc)[:160]})
            continue
        visitor = QueryRiskVisitor()
        visitor.visit(tree)
        for item in visitor.findings:
            item["file"] = str(path.relative_to(base))
            findings.append(item)
    return {"root": str(base), "files_scanned": scanned, "findings": findings,
            "note": "Static indicators only; manually review query construction and parameter binding."}

def export_local_sqlite(db_path, output_dir="omega_exports"):
    source = Path(db_path).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() not in (".db", ".sqlite", ".sqlite3"):
        raise ValueError("Choose an existing local SQLite .db, .sqlite or .sqlite3 file.")
    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    exported = []
    connection = sqlite3.connect("file:{}?mode=ro".format(source.as_posix()), uri=True)
    try:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        for (table,) in tables:
            safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in table)
            rows = connection.execute('SELECT * FROM "{}"'.format(table.replace('"', '""')))
            columns = [item[0] for item in rows.description]
            records = rows.fetchall()
            json_path = destination / (safe_name + ".json")
            json_path.write_text(json.dumps(
                [dict(zip(columns, row)) for row in records],
                ensure_ascii=False, indent=2, default=str
            ), encoding="utf-8")
            csv_path = destination / (safe_name + ".csv")
            with csv_path.open("w", newline="", encoding="utf-8-sig") as stream:
                writer = csv.writer(stream)
                writer.writerow(columns)
                writer.writerows(records)
            exported.append({"table": table, "rows": len(records),
                             "json": str(json_path), "csv": str(csv_path)})
    finally:
        connection.close()
    return {"database": str(source), "tables_exported": exported,
            "note": "Read-only export from the local database supplied by the operator."}

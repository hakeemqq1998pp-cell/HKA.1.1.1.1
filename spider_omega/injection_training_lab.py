"""Local-only SQL injection training lab.

Runs against an in-memory SQLite database. It never accepts a network target,
never reads external databases, and never exports data.
"""
import sqlite3


def run_sql_injection_lab():
    db = sqlite3.connect(":memory:")
    try:
        db.execute("CREATE TABLE demo_users (id INTEGER PRIMARY KEY, username TEXT, role TEXT)")
        db.executemany(
            "INSERT INTO demo_users(username, role) VALUES (?, ?)",
            [("alice", "user"), ("bob", "user"), ("admin", "administrator")],
        )
        test_input = "' OR '1'='1"

        vulnerable_sql = (
            "SELECT username, role FROM demo_users WHERE username = '"
            + test_input
            + "'"
        )
        vulnerable_rows = db.execute(vulnerable_sql).fetchall()

        safe_sql = "SELECT username, role FROM demo_users WHERE username = ?"
        safe_rows = db.execute(safe_sql, (test_input,)).fetchall()

        return {
            "lab": "in-memory SQLite only",
            "test_input": test_input,
            "vulnerable_query_rows": vulnerable_rows,
            "parameterized_query_rows": safe_rows,
            "vulnerable_query_count": len(vulnerable_rows),
            "parameterized_query_count": len(safe_rows),
            "lesson": (
                "String concatenation allowed the test input to alter SQL logic; "
                "the parameterized query treated it as data."
            ),
        }
    finally:
        db.close()

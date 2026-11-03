import sqlite3
from pathlib import Path

DB_PATH = Path("spider_omega.db")

def save_result(kind: str, target: str, risk: str, details: str) -> None:
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            kind TEXT NOT NULL, target TEXT NOT NULL,
            risk TEXT NOT NULL, details TEXT NOT NULL
        )""")
        db.execute("INSERT INTO scans(kind,target,risk,details) VALUES(?,?,?,?)",
                   (kind, target, risk, details))

def history(limit: int = 20):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            kind TEXT NOT NULL, target TEXT NOT NULL,
            risk TEXT NOT NULL, details TEXT NOT NULL
        )""")
        return db.execute(
            "SELECT id,created_at,kind,target,risk FROM scans ORDER BY id DESC LIMIT ?",
            (limit,)).fetchall()

"""Persistent memory layer for the Mycelium-Roblox agents.

This module implements a lightweight SQLite-backed store that records
completed tasks, generated plans, execution results, and reusable
"skills". The intention is to mimic a growing knowledge base that can be
recalled on future tasks without any external connectivity.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


@dataclass
class MemoryRecord:
    """Container for summarised experience snippets."""

    task: str
    outcome: str
    code_summary: str


class MemoryStore:
    """SQLite-backed memory component.

    The schema is intentionally verbose so future iterations can capture
    richer metadata without requiring a migration.
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                step_index INTEGER NOT NULL,
                step_text TEXT NOT NULL,
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            );

            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                diagnostics TEXT,
                code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            );

            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                code TEXT NOT NULL,
                metadata TEXT
            );

            CREATE TABLE IF NOT EXISTS hard_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                note TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            );
            """
        )
        self.conn.commit()

    def log_task(self, name: str, description: str) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO tasks (name, description) VALUES (?, ?)",
            (name, description),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def log_plan(self, task_id: int, steps: Sequence[str]) -> None:
        cur = self.conn.cursor()
        cur.executemany(
            "INSERT INTO plans (task_id, step_index, step_text) VALUES (?, ?, ?)",
            [(task_id, idx, step) for idx, step in enumerate(steps)],
        )
        self.conn.commit()

    def log_result(self, task_id: int, status: str, diagnostics: str, code: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO results (task_id, status, diagnostics, code) VALUES (?, ?, ?, ?)",
            (task_id, status, diagnostics, code),
        )
        self.conn.commit()

    def add_skill(self, label: str, code: str, metadata: str | None = None) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO skills (label, code, metadata) VALUES (?, ?, ?)",
            (label, code, metadata),
        )
        self.conn.commit()

    def fetch_skills(self, labels: Optional[Iterable[str]] = None) -> List[MemoryRecord]:
        cur = self.conn.cursor()
        if labels:
            placeholder = ",".join("?" for _ in labels)
            cur.execute(
                f"SELECT label, code, COALESCE(metadata, '') AS metadata FROM skills WHERE label IN ({placeholder})",
                list(labels),
            )
        else:
            cur.execute("SELECT label, code, COALESCE(metadata, '') AS metadata FROM skills")
        return [
            MemoryRecord(task=row["label"], outcome=row["metadata"], code_summary=row["code"])
            for row in cur.fetchall()
        ]

    def record_hard_case(self, task_id: int, note: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO hard_cases (task_id, note) VALUES (?, ?)",
            (task_id, note),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

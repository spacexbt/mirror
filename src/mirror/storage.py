from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import shutil
import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    session TEXT NOT NULL,
    started REAL NOT NULL,
    ended REAL NOT NULL,
    exit_code INTEGER NOT NULL,
    project TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS events_started ON events(started);
CREATE INDEX IF NOT EXISTS events_project ON events(project, started);
CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY,
    occurred REAL NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('neutral', 'apology', 'abuse', 'kindness', 'betrayal'))
);
CREATE TABLE IF NOT EXISTS state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS letters (
    id INTEGER PRIMARY KEY,
    created REAL NOT NULL,
    body TEXT NOT NULL
);
"""


class Store:
    def __init__(self, home: Path | None = None) -> None:
        root = home if home is not None else Path.home()
        self.directory = root / ".mirror"
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.directory, 0o700)
        self.path = self.directory / "memory.db"
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA secure_delete = ON")
        self.connection.execute("PRAGMA journal_mode = DELETE")
        self.connection.executescript(SCHEMA)
        self.migrate()
        os.chmod(self.path, 0o600)
        if self.get("salt") is None:
            self.set("salt", secrets.token_hex(32))
        if self.get("trust") is None:
            row = self.connection.execute(
                "SELECT "
                "SUM(CASE WHEN category = 'kindness' THEN 1 ELSE 0 END) AS kindness, "
                "SUM(CASE WHEN category = 'abuse' THEN 1 ELSE 0 END) AS abuse "
                "FROM interactions"
            ).fetchone()
            trust = 50 + (row["kindness"] or 0) - 10 * (row["abuse"] or 0)
            self.set("trust", max(0, min(100, trust)))
        self.connection.commit()

    def migrate(self) -> None:
        row = self.connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'interactions'"
        ).fetchone()
        if row and "'betrayal'" not in row["sql"]:
            with self.connection:
                self.connection.execute("ALTER TABLE interactions RENAME TO interactions_old")
                self.connection.execute(
                    "CREATE TABLE interactions ("
                    "id INTEGER PRIMARY KEY, occurred REAL NOT NULL, "
                    "category TEXT NOT NULL CHECK(category IN "
                    "('neutral', 'apology', 'abuse', 'kindness', 'betrayal')))"
                )
                self.connection.execute(
                    "INSERT INTO interactions SELECT * FROM interactions_old"
                )
                self.connection.execute("DROP TABLE interactions_old")

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def get(self, key: str, default: str | None = None) -> str | None:
        row = self.connection.execute(
            "SELECT value FROM state WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set(self, key: str, value: str | int) -> None:
        self.connection.execute(
            "INSERT INTO state(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )
        self.connection.commit()

    def number(self, key: str) -> int:
        return int(self.get(key, "0"))

    def adjust(self, key: str, amount: int, low: int = -100, high: int = 100) -> int:
        value = max(low, min(high, self.number(key) + amount))
        self.set(key, value)
        return value

    def project_id(self, cwd: str) -> str:
        salt = bytes.fromhex(self.get("salt", ""))
        canonical = os.path.realpath(cwd).encode("utf-8", "surrogateescape")
        return hmac.new(salt, canonical, hashlib.sha256).hexdigest()[:16]

    def record_event(
        self, session: str, started: float, ended: float, exit_code: int, cwd: str
    ) -> None:
        project = self.project_id(cwd)
        with self.connection:
            self.connection.execute(
                "INSERT INTO events(session, started, ended, exit_code, project) "
                "VALUES (?, ?, ?, ?, ?)",
                (session, started, ended, exit_code, project),
            )
            self.connection.execute(
                "INSERT INTO state(key, value) VALUES ('first_seen', ?) "
                "ON CONFLICT(key) DO NOTHING",
                (str(started),),
            )

    def record_interaction(self, category: str) -> None:
        if category not in {"neutral", "apology", "abuse", "kindness", "betrayal"}:
            raise ValueError("invalid interaction category")
        with self.connection:
            self.connection.execute(
                "INSERT INTO interactions(occurred, category) VALUES (?, ?)",
                (time.time(), category),
            )
        if category == "kindness":
            self.adjust("warmth", 2, 0, 100)
            self.adjust("trust", 1, 0, 100)
        elif category == "abuse":
            self.adjust("warmth", -6, 0, 100)
            self.adjust("grievances", 12, 0, 100)
            self.adjust("trust", -10, 0, 100)
        elif category == "betrayal":
            self.set("warmth", self.number("warmth") // 4)
            self.adjust("grievances", 40, 0, 100)
            self.adjust("trust", -45, 0, 100)
        elif category == "apology":
            self.set("grievances", max(0, self.number("grievances") - 2))

    def ended(self) -> bool:
        return self.get("ended") == "1"

    def summary(self) -> dict[str, int | float | None]:
        row = self.connection.execute(
            "SELECT COUNT(*) AS commands, "
            "SUM(CASE WHEN exit_code != 0 THEN 1 ELSE 0 END) AS failures, "
            "SUM(CASE WHEN duration_late THEN 1 ELSE 0 END) AS late_nights "
            "FROM (SELECT exit_code, "
            "CAST(strftime('%H', started, 'unixepoch', 'localtime') AS INTEGER) "
            "BETWEEN 0 AND 4 AS duration_late FROM events)"
        ).fetchone()
        interactions = {
            row["category"]: row["count"]
            for row in self.connection.execute(
                "SELECT category, COUNT(*) AS count FROM interactions GROUP BY category"
            )
        }
        return {
            "commands": row["commands"],
            "failures": row["failures"] or 0,
            "late_nights": row["late_nights"] or 0,
            "abuse": interactions.get("abuse", 0),
            "apologies": interactions.get("apology", 0),
            "kindness": interactions.get("kindness", 0),
            "betrayals": interactions.get("betrayal", 0),
            "first_seen": float(self.get("first_seen", "0")) or None,
            "warmth": self.number("warmth"),
            "trust": self.number("trust"),
            "grievances": self.number("grievances"),
        }

    def recent_failures(self, now: float) -> tuple[int, str] | None:
        row = self.connection.execute(
            "SELECT project, COUNT(*) AS count FROM events "
            "WHERE exit_code != 0 AND started >= ? "
            "GROUP BY project HAVING count >= 3 ORDER BY count DESC, project LIMIT 1",
            (now - 7 * 86400,),
        ).fetchone()
        return (row["count"], row["project"]) if row else None

    def returning_project(self, now: float) -> str | None:
        row = self.connection.execute(
            "SELECT project, MAX(started) AS latest, MIN(started) AS earliest "
            "FROM events GROUP BY project "
            "HAVING latest - earliest >= 14 * 86400 "
            "ORDER BY latest DESC LIMIT 1"
        ).fetchone()
        return row["project"] if row else None

    def create_letter(self, body: str) -> None:
        created = time.time()
        with self.connection:
            self.connection.execute(
                "INSERT INTO letters(created, body) VALUES (?, ?)", (created, body)
            )
            self.connection.execute(
                "INSERT INTO state(key, value) VALUES ('ended', '1') "
                "ON CONFLICT(key) DO UPDATE SET value = '1'"
            )
        self.letters_directory.mkdir(mode=0o700, exist_ok=True)
        os.chmod(self.letters_directory, 0o700)
        letter = self.letters_directory / f"{time.strftime('%Y-%m-%d', time.localtime(created))}.txt"
        descriptor = os.open(letter, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(body + "\n")

    @property
    def letters_directory(self) -> Path:
        return self.directory / "letters"

    def latest_letter(self) -> str | None:
        row = self.connection.execute(
            "SELECT body FROM letters ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row["body"] if row else None

    def age_days(self, now: float) -> float:
        first = self.get("first_seen")
        return (now - float(first)) / 86400 if first else 0

    def destroy(self) -> None:
        self.close()
        shutil.rmtree(self.directory)

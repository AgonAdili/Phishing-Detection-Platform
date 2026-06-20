from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "app.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS departments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    department    TEXT NOT NULL,
    role          TEXT NOT NULL,
    -- hidden susceptibility trait (0..1) used by the simulation engine only
    susceptibility REAL NOT NULL DEFAULT 0.4,
    risk_score    REAL NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS templates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL,          -- credential, invoice, it_support, hr, delivery, ceo_fraud
    difficulty  TEXT NOT NULL,          -- easy, medium, hard
    sender      TEXT NOT NULL,
    subject     TEXT NOT NULL,
    body        TEXT NOT NULL,
    indicators  TEXT NOT NULL DEFAULT '[]',  -- JSON list of red-flag tags
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS campaigns (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    template_id  INTEGER NOT NULL,
    difficulty   TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'completed',  -- draft, running, completed
    target_count INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL,
    FOREIGN KEY (template_id) REFERENCES templates (id)
);

-- One row per (campaign, user) target, tracking the furthest action reached.
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL,
    user_id     INTEGER NOT NULL,
    sent        INTEGER NOT NULL DEFAULT 1,
    opened      INTEGER NOT NULL DEFAULT 0,
    clicked     INTEGER NOT NULL DEFAULT 0,
    submitted   INTEGER NOT NULL DEFAULT 0,
    reported    INTEGER NOT NULL DEFAULT 0,
    timestamp   TEXT NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS training_modules (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key         TEXT NOT NULL UNIQUE,   -- maps to indicator tags
    title       TEXT NOT NULL,
    topic       TEXT NOT NULL,
    description TEXT NOT NULL,
    minutes     INTEGER NOT NULL DEFAULT 5
);

CREATE TABLE IF NOT EXISTS training_assignments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    module_key  TEXT NOT NULL,
    reason      TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'assigned',  -- assigned, completed, overdue
    assigned_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (module_key) REFERENCES training_modules (key)
);
"""


def _connect() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = _connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def reset_db() -> None:
    """Drop the whole database file (used by the seeder)."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

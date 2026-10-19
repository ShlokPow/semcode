"""Connection helper and the forward-only migration runner (SPEC.md §4)."""

from pathlib import Path

import psycopg

from semcode.core.config import settings

# ponytail: resolved from the source tree, so it only works from a checkout (dev + the Docker
# image both have one). Move into the package as package data if semcode is ever pip-installed.
MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"

TABLES = ("repos", "files", "chunks", "chunk_embeddings", "embedding_cache")


def connect() -> psycopg.Connection:
    # Autocommit, so `with conn.transaction()` is a real transaction, not a savepoint.
    return psycopg.connect(settings.database_url, autocommit=True)


def migrate(conn: psycopg.Connection) -> list[str]:
    """Apply every migrations/*.sql not yet recorded, in filename order. Returns names applied."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        " name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    )
    done = {name for (name,) in conn.execute("SELECT name FROM schema_migrations")}
    applied = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.name in done:
            continue
        # One transaction per file: a failing migration leaves no half-applied schema behind.
        with conn.transaction():
            conn.execute(path.read_text())
            conn.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (path.name,))
        applied.append(path.name)
    return applied


def reset(conn: psycopg.Connection) -> list[str]:
    """Drop everything (including the paid-for embedding cache) and re-migrate."""
    conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public")
    return migrate(conn)


def stats(conn: psycopg.Connection) -> dict[str, int]:
    # Table names come from the TABLES constant, never from input, so f-string SQL is safe here.
    return {t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in TABLES}

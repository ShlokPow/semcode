"""Phase 0 smoke test: schema applies cleanly, idempotently, and the CLI wires up.

Needs a running Postgres at DATABASE_URL (docker compose up -d). Non-destructive: it only runs
pending migrations, so it is safe against a dev DB that already holds an index.
"""

from typer.testing import CliRunner

from semcode.cli import app
from semcode.core import db


def test_migrate_creates_schema_and_is_idempotent():
    with db.connect() as conn:
        db.migrate(conn)
        assert db.migrate(conn) == []  # second run applies nothing

        tables = {r[0] for r in conn.execute("SELECT tablename FROM pg_tables")}
        assert set(db.TABLES) <= tables

        exts = {r[0] for r in conn.execute("SELECT extname FROM pg_extension")}
        assert {"vector", "pg_trgm"} <= exts

        indexes = {r[0] for r in conn.execute("SELECT indexdef FROM pg_indexes")}
        assert any("USING hnsw" in i for i in indexes)
        assert any("gin_trgm_ops" in i for i in indexes)

        assert set(db.stats(conn)) == set(db.TABLES)


def test_cli_help():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "db" in result.output

import typer

from semcode.core import db

app = typer.Typer(no_args_is_help=True, help="Hybrid semantic + keyword code search.")
db_app = typer.Typer(no_args_is_help=True, help="Manage the Postgres schema.")
app.add_typer(db_app, name="db")


@db_app.command()
def init() -> None:
    """Apply pending migrations."""
    with db.connect() as conn:
        applied = db.migrate(conn)
    typer.echo(f"applied: {', '.join(applied)}" if applied else "up to date")


@db_app.command()
def reset(yes: bool = typer.Option(False, "--yes", help="Skip the confirmation prompt.")) -> None:
    """Drop all data, including the embedding cache, and re-create the schema."""
    if not yes:
        typer.confirm("This deletes every index and the embedding cache. Continue?", abort=True)
    with db.connect() as conn:
        db.reset(conn)
    typer.echo("reset complete")


@db_app.command()
def stats() -> None:
    """Row counts per table."""
    with db.connect() as conn:
        for table, n in db.stats(conn).items():
            typer.echo(f"{table:<18}{n}")

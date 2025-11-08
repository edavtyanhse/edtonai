from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text


def test_initial_migration_sql_executes() -> None:
    sql_path = Path(__file__).resolve().parents[2] / "db" / "001_init.sql"
    sql = sql_path.read_text(encoding="utf-8")

    sanitized: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped:
            sanitized.append(line)
            continue
        if stripped.lower().startswith("create extension"):
            continue
        sanitized.append(line)

    normalized = "\n".join(sanitized)
    normalized = (
        normalized.replace(" jsonb", " json")
        .replace(" uuid", " text")
        .replace("::jsonb", "")
        .replace("numeric", "real")
        .replace("timestamptz", "timestamp")
        .replace("default gen_random_uuid()", "")
        .replace("default now()", "default CURRENT_TIMESTAMP")
    )

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    statements = [stmt.strip() for stmt in normalized.split(";") if stmt.strip()]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))

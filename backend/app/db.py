from __future__ import annotations
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import os

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy import create_engine

# гарантированно грузим backend/.env
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

_engine: Optional[Engine] = None

def get_engine() -> Engine:
    global _engine
    if _engine is not None:
        return _engine
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL не задан в backend/.env")
    _engine = create_engine(dsn, pool_pre_ping=True)
    return _engine

def db_health() -> bool:
    eng = get_engine()
    with eng.connect() as conn:
        return conn.execute(text("select 1")).scalar() == 1
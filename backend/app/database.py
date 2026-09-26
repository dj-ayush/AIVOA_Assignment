from __future__ import annotations

import json
from typing import Any, Dict, List
from urllib.parse import unquote, urlparse

import mysql.connector
from mysql.connector import MySQLConnection

from .config import DATABASE_URL


def is_database_configured() -> bool:
    return bool(DATABASE_URL)


def _connection_config() -> Dict[str, Any]:
    parsed = urlparse(DATABASE_URL)
    if parsed.scheme not in {"mysql", "mysql+mysqlconnector"}:
        raise ValueError("DATABASE_URL must use mysql:// or mysql+mysqlconnector://")
    database = parsed.path.lstrip("/")
    if not database:
        raise ValueError("DATABASE_URL must include a database name")
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": database,
    }


def _connect() -> MySQLConnection:
    return mysql.connector.connect(**_connection_config())


def ensure_deviation_table() -> None:
    if not is_database_configured():
        return
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS deviations (
                    id VARCHAR(32) PRIMARY KEY,
                    committed_at VARCHAR(40) NOT NULL,
                    form JSON NOT NULL,
                    risk_assessment JSON NOT NULL
                )
                """
            )
        conn.commit()


def save_deviation_record(record: Dict[str, Any]) -> None:
    ensure_deviation_table()
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO deviations (id, committed_at, form, risk_assessment)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    record["id"],
                    record["committed_at"],
                    json.dumps(record["form"]),
                    json.dumps(record["risk_assessment"]),
                ),
            )
        conn.commit()


def _decode_json(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        return json.loads(value)
    return value


def load_deviation_records() -> List[Dict[str, Any]]:
    ensure_deviation_table()
    with _connect() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                """
                SELECT id, committed_at, form, risk_assessment
                FROM deviations
                ORDER BY committed_at DESC
                """
            )
            records = []
            for row in cur.fetchall():
                records.append(
                    {
                        "id": row["id"],
                        "committed_at": row["committed_at"],
                        "form": _decode_json(row["form"]),
                        "risk_assessment": _decode_json(row["risk_assessment"]),
                    }
                )
            return records

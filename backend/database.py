import os
import sqlite3
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

FLUXBASE_URL = os.getenv("FLUXBASE_URL", "https://fluxbase.vercel.app/api/execute-sql")
API_KEY = os.getenv("FLUXBASE_API_KEY")
PROJECT_ID = os.getenv("FLUXBASE_PROJECT_ID")
USE_LOCAL_DB = os.getenv("USE_LOCAL_DB", "true").lower() in {"1", "true", "yes"}
LOCAL_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heart_disease.db")


def _local_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(LOCAL_DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
        """
    )
    connection.commit()
    return connection


def _run_local_query(sql: str) -> list[dict[str, Any]]:
    with _local_connection() as connection:
        cursor = connection.execute(sql)
        if cursor.description is None:
            connection.commit()
            return []
        return [dict(row) for row in cursor.fetchall()]


def _run_fluxbase_query(sql: str) -> list[dict[str, Any]]:
    if not API_KEY or not PROJECT_ID:
        raise RuntimeError("Fluxbase credentials not found in environment variables.")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"projectId": PROJECT_ID, "query": sql}

    try:
        response = requests.post(
            FLUXBASE_URL,
            json=payload,
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise RuntimeError(f"Unable to reach Fluxbase: {exc}") from exc
    except ValueError as exc:
        raise RuntimeError("Fluxbase returned an invalid response.") from exc

    if not data.get("success"):
        error_msg = data.get("error", {}).get("message", "Unknown error")
        raise RuntimeError(f"Fluxbase Error: {error_msg}")

    result = data.get("result", {})
    return result.get("rows", [])


def run_query(sql: str) -> list[dict[str, Any]]:
    if USE_LOCAL_DB:
        return _run_local_query(sql)
    return _run_fluxbase_query(sql)


def get_user_by_email(email: str) -> dict[str, Any] | None:
    escaped_email = email.replace("'", "''")
    rows = run_query(f"SELECT * FROM users WHERE email = '{escaped_email}'")
    return rows[0] if rows else None


def create_user(name: str, email: str, password_hash: str) -> list[dict[str, Any]]:
    escaped_name = name.replace("'", "''")
    escaped_email = email.replace("'", "''")
    escaped_hash = password_hash.replace("'", "''")
    return run_query(
        "INSERT INTO users (name, email, password_hash) "
        f"VALUES ('{escaped_name}', '{escaped_email}', '{escaped_hash}')"
    )

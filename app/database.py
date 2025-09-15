import re
import os
import sqlite3
from contextlib import contextmanager
from typing import Optional, Dict, List
import logging

import bcrypt


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def get_db_path():
    return os.path.join(os.path.dirname(__file__), "..", "data", "database.db")


def validate_table_name(table_name: str) -> bool:
    return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name))


def validate_column_name(column_name: str) -> bool:
    return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", column_name))


@contextmanager
def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Failed to connect db: {e}")
        raise e
    finally:
        if conn:
            conn.close()


def safe_execute(
    conn: sqlite3.Connection, query: str, params: tuple = ()
) -> Optional[sqlite3.Cursor]:
    try:
        logger.debug(f"Executing query: {query.split()[0]}...")

        cursor = conn.execute(query, params)
        return cursor
    except sqlite3.Error as e:
        logger.error(f"SQL execution error: {e}, Query: {query}")
        raise


def safe_executemany(
    conn: sqlite3.Connection, query: str, params_list: List[tuple]
) -> None:
    try:
        logger.debug(f"Executing many queries: {query.split()[0]}...")
        conn.executemany(query, params_list)
    except sqlite3.Error as e:
        logger.error(f"SQL executemany error: {e}, Query: {query}")
        raise


def safe_fetchone(
    conn: sqlite3.Connection, query: str, params: tuple = ()
) -> Optional[Dict]:
    cursor = safe_execute(conn, query, params)
    result = cursor.fetchone()
    return dict(result) if result else None


def safe_fetchall(
    conn: sqlite3.Connection, query: str, params: tuple = ()
) -> List[Dict]:
    cursor = safe_execute(conn, query, params)
    return [dict(row) for row in cursor.fetchall()]


def safe_insert(conn: sqlite3.Connection, table: str, data: Dict) -> int:
    if not validate_table_name(table):
        raise ValueError(f"Invalid table name: {table}")

    columns = []
    placeholders = []
    values = []

    for column, value in data.items():
        if not validate_column_name(column):
            raise ValueError(f"Invalid column name: {column}")
        columns.append(column)
        placeholders.append("?")
        values.append(value)

    query = (
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    )
    cursor = safe_execute(conn, query, tuple(values))
    conn.commit()
    return cursor.lastrowid


def safe_select(
    conn: sqlite3.Connection,
    table: str,
    where: Optional[Dict] = None,
    columns: List[str] = ["*"],
) -> List[Dict]:
    if not validate_table_name(table):
        raise ValueError(f"Invalid table name: {table}")

    for column in columns:
        if column != "*" and not validate_column_name(column):
            raise ValueError(f"Invalid column name: {column}")

    column_list = ", ".join(columns)
    query = f"SELECT {column_list} FROM {table}"
    params = ()

    if where:
        where_clauses = []
        where_values = []
        for column, value in where.items():
            if not validate_column_name(column):
                raise ValueError(f"Invalid column name: {column}")
            where_clauses.append(f"{column} = ?")
            where_values.append(value)

        query += f" WHERE {' AND '.join(where_clauses)}"
        params = tuple(where_values)

    return safe_fetchall(conn, query, params)


def init_db():
    with get_db_connection() as conn:
        safe_execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                CHECK (LENGTH(username) >= 3 AND LENGTH(username) <= 50),
                CHECK (role IN ('user', 'admin'))
            )
        """,
        )

        conn.commit()


def insert_initial_data():
    with get_db_connection() as conn:
        users_count = safe_fetchone(conn, "SELECT COUNT(*) as count FROM users")[
            "count"
        ]

        if users_count == 0:
            users = [
                {
                    "username": "admin",
                    "password_hash": bcrypt.hashpw(
                        "admin123".encode("utf-8"), bcrypt.gensalt()
                    ),
                    "role": "admin",
                },
                {
                    "username": "user",
                    "password_hash": bcrypt.hashpw(
                        "user123".encode("utf-8"), bcrypt.gensalt()
                    ),
                    "role": "user",
                },
            ]

            for user in users:
                safe_insert(conn, "users", user)

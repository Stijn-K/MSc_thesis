from __future__ import annotations

import sqlite3

_DB = '../db/db.sqlite'


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def initialize_db() -> None:
    with sqlite3.connect(_DB) as conn:
        with open('../db/init.sql') as f:
            conn.executescript(f.read())


def get_user_by_credentials(username: str, password: str) -> dict:
    with sqlite3.connect(_DB) as conn:
        conn.row_factory = dict_factory
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM users WHERE username="{username}" AND password="{password}"')
        return cur.fetchone()


def get_user_by_cookie(cookie: str) -> dict:
    with sqlite3.connect(_DB) as conn:
        conn.row_factory = dict_factory
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM users WHERE cookie="{cookie}"')
        return cur.fetchone()


def set_user_cookie(username: str, cookie: str) -> None:
    with sqlite3.connect(_DB) as conn:
        cur = conn.cursor()
        cur.execute(f'UPDATE users SET cookie="{cookie}" WHERE username="{username}"')


def get_user_challenges(user_id: int) -> list[dict[str, str]] | None:
    with sqlite3.connect(_DB) as conn:
        conn.row_factory = dict_factory
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM challenges WHERE user_id={user_id}')
        return cur.fetchall()


def set_user_challenges(user_id: int, challenges: dict[str, str]) -> None:
    with sqlite3.connect(_DB) as conn:
        cur = conn.cursor()
        for challenge, response in challenges.items():
            cur.execute(f'INSERT INTO challenges (user_id, challenge, response) VALUES ({user_id}, "{challenge}", "{response}")')


def remove_user_challenge(challenge_id: int) -> None:
    with sqlite3.connect(_DB) as conn:
        cur = conn.cursor()
        cur.execute(f'DELETE FROM challenges WHERE id={challenge_id}')


def verify_challenge(user_id: int, challenge: str, response: str) -> dict[str, str]:
    with sqlite3.connect(_DB) as conn:
        conn.row_factory = dict_factory
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM challenges WHERE user_id={user_id} AND challenge="{challenge}" AND response="{response}"')
        return cur.fetchone()

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


def set_user_credentials_id(username: str, cid: str) -> None:
    with sqlite3.connect(_DB) as conn:
        cur = conn.cursor()
        cur.execute(f'UPDATE users SET credentials_id="{cid}" WHERE username="{username}"')


def get_user_by_credentials_id(cid: str) -> dict:
    with sqlite3.connect(_DB) as conn:
        conn.row_factory = dict_factory
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM users WHERE credentials_id="{cid}"')
        return cur.fetchone()


def get_user_by_username(username: str) -> dict:
    with sqlite3.connect(_DB) as conn:
        conn.row_factory = dict_factory
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM users WHERE username="{username}"')
        return cur.fetchone()

from __future__ import annotations
import os
import time

import hmac
import hashlib

import db_helpers as db


_SERVER_KEY: bytes | None = None
_EXPIRES_SECONDS: int = 60 * 60 * 24


def initialize() -> None:
    global _SERVER_KEY
    _SERVER_KEY = os.urandom(32)


def generate_cookie(user: dict, **kwargs) -> str:

    expires = int(time.time()) + _EXPIRES_SECONDS

    k = hmac.new(_SERVER_KEY, f"{user['username']}|{expires}".encode(), hashlib.sha256).digest()
    _hmac = hmac.new(k, f"{user['username']}|{expires}".encode(), hashlib.sha256).hexdigest()
    cookie = f"{user['username']}|{expires}|{_hmac}"

    db.set_user_cookie(user['username'], cookie)

    return cookie


def verify_cookie(cookie: str, **kwargs) -> tuple[bool, dict | str | None]:
    user = db.get_user_by_cookie(cookie)

    if not user:
        return False, 'Invalid cookie'

    _username, _expires, _hmac = cookie.split('|')

    if int(time.time()) > int(_expires):
        return False, 'Cookie expired'

    k = hmac.new(_SERVER_KEY, f"{_username}|{_expires}".encode(), hashlib.sha256).digest()
    _hmac_check = hmac.new(k, f"{_username}|{_expires}".encode(), hashlib.sha256).hexdigest()

    if _hmac_check != _hmac:
        return False, 'Invalid hmac'

    return True, user


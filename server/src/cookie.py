from __future__ import annotations

from typing import Optional

import src.db_helpers as db


def generate_cookie(user: dict, **kwargs) -> str:
    cookie = 'this_is_a_cookie'

    db.set_user_cookie(user['username'], cookie)

    return cookie


def verify_cookie(cookie: str, **kwargs) -> tuple[bool, dict | str | None]:
    user = db.get_user_by_cookie(cookie)

    if not user:
        return False, 'Invalid cookie'

    return True, user


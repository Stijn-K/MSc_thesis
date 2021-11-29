from typing import Optional

import db_helpers as db


def generate_cookie(user: dict, **kwargs) -> str:
    cookie = 'this_is_a_session_cookie'

    db.set_user_cookie(user['username'], cookie)

    return cookie


def verify_cookie(cookie: str, **kwargs) -> Optional[dict]:
    user = db.get_user_by_cookie(cookie)

    return user


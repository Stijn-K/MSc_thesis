from __future__ import annotations

from typing import Optional

import db_helpers as db
import random


def generate_cookie(user: dict, **kwargs) -> str:
    cookie = 'this_is_a_session_cookie'

    db.set_user_cookie(user['username'], cookie)

    challenges = kwargs['challenges']
    db.set_user_challenges(user['id'], challenges)

    return cookie


def get_user_from_cookie(cookie: str) -> Optional[dict]:
    user = db.get_user_by_cookie(cookie)
    if not user:
        return None

    return user


def verify_cookie(cookie: str, **kwargs) -> tuple[bool, dict | str | None]:
    user = db.get_user_by_cookie(cookie)
    if not user:
        return False, 'Invalid cookie'

    challenge, response = kwargs['challenge_response']
    result = db.verify_challenge(user['id'], challenge, response)
    if not result:
        return False, 'Invalid challenge response'

    db.remove_user_challenge(result['id'])
    return True, user


def get_challenge(user_id: int) -> str | None:
    challenges = db.get_user_challenges(user_id)
    if not challenges:
        return

    challenge = random.choice(challenges)
    return challenge['challenge']


def generate_challenges(n: int = 10, length: int = 10):
    return [
        ''.join([str(random.randint(0, 1)) for _ in range(length)]) for _ in range(n)
    ]

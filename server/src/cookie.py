from __future__ import annotations
import db_helpers as db

import json
import hashlib


def generate_cookie(user: dict, **kwargs) -> str:
    fingerprint = kwargs['fingerprint']
    fingerprint_json = json.dumps(fingerprint, sort_keys=True)
    fingerprint_hash = hashlib.md5(fingerprint_json.encode()).hexdigest()

    cookie = 'this_is_a_session_cookie'
    db.set_user_cookie(user['username'], cookie)

    db.set_user_fingerprint(user['username'], fingerprint_hash)

    return cookie


def verify_cookie(cookie: str, **kwargs) -> tuple[bool, dict | str | None]:
    fingerprint = kwargs['fingerprint']
    fingerprint_json = json.dumps(fingerprint, sort_keys=True)
    fingerprint_hash = hashlib.md5(fingerprint_json.encode()).hexdigest()

    user = db.get_user_by_cookie(cookie)
    if not user:
        return False, 'Invalid cookie'
    elif user['fingerprint'] == fingerprint_hash:
        return True, user
    else:
        return False, 'Invalid fingerprint'


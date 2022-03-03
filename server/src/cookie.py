from __future__ import annotations

import os
from cryptography.hazmat.primitives import hashes
import hashlib
import hmac

from OpenSSL.crypto import X509

import db_helpers as db

_LONG_TERM_KEY: bytes | None = None


def initialize_obc() -> None:
    global _LONG_TERM_KEY
    _LONG_TERM_KEY = os.urandom(32)


def generate_cookie(user: dict, certificate: X509) -> str:
    cert = certificate.to_cryptography()

    v = 'this_is_a_session_cookie'
    f = cert.fingerprint(hashes.SHA256())

    m = hmac.new(_LONG_TERM_KEY, v.encode() + f, hashlib.sha256).hexdigest()

    cookie = f'{v},{m}'
    db.set_user_cookie(user['username'], cookie)

    return cookie


def verify_cookie(cookie: str, certificate: X509) -> tuple[bool, dict | str | None]:
    v_client, m_client = cookie.split(',')

    cert = certificate.to_cryptography()
    f = cert.fingerprint(hashes.SHA256())

    m = hmac.new(_LONG_TERM_KEY, v_client.encode() + f, hashlib.sha256).hexdigest()

    if m != m_client:
        return False, 'Invalid certificate'

    user = db.get_user_by_cookie(cookie)
    if not user:
        return False, 'Invalid cookie'

    return True, user



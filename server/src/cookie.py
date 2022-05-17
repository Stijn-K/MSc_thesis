from __future__ import annotations

import src.db_helpers as db

import os
import time
import hashlib
import hmac
from cryptography.fernet import Fernet, InvalidToken
from base64 import urlsafe_b64encode as b64encode

_LONG_TERM_KEY: bytes | None = None
_SESSION_EXP = 1672527600


def initialize_otc():
    global _LONG_TERM_KEY
    _LONG_TERM_KEY = os.urandom(32)


def generate_otc(user: dict):
    k_s = os.urandom(32).hex()
    n_s = os.urandom(32)
    t_s = _SESSION_EXP
    cid = os.urandom(32).hex()
    uid = user['username']

    key = _bytes_xor(_LONG_TERM_KEY, n_s)

    f = Fernet(b64encode(key))

    ticket = f.encrypt(f'{cid}|{uid}|{k_s}|{t_s}'.encode()).hex()

    db.set_user_credentials_id(user['username'], cid)

    return cid, n_s.hex(), k_s, t_s, ticket


def verify_otc(cid, n_s, t_h, h, ticket, url, body):
    if int(time.time()) > int(t_h):
        return False, 'Ticket expired'

    key = _bytes_xor(_LONG_TERM_KEY, bytes.fromhex(n_s))
    f = Fernet(b64encode(key))

    try:
        _cid, _uid, _k_s, _t_s = f.decrypt(bytes.fromhex(ticket)).decode().split('|')
    except (InvalidToken, TypeError, ValueError) as e:
        return False, 'Invalid ticket'

    user = db.get_user_by_credentials_id(_cid)
    if cid != _cid or user['username'] != _uid:
        return False, 'Invalid OTC credentials'

    msg = f'{url}|{t_h}|{body}'.encode()
    _h = hmac.new(bytes.fromhex(_k_s), msg, hashlib.sha256).hexdigest()
    if _h != h:
        return False, 'Invalid request'

    return True, user


def _bytes_xor(a: bytes, b: bytes):
    return bytes(x ^ y for x, y in zip(a, b))

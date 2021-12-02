from typing import Optional

import os
import sys

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

_SERVER = os.getenv('SERVER', 'localhost')
_URL = f'https://{_SERVER}:5000'


def is_alive() -> bool:
    response = requests.get(f'{_URL}/alive', verify=False)
    return response.status_code == 204


def do_login() -> str:
    response = requests.get(f'{_URL}/login', params={
        'username': 'test_user',
        'password': '12345'
    }, verify=False, allow_redirects=False)

    cookies = None

    if response.status_code == 302:
        cookies = response.cookies
        redirect = response.headers['Location']
        _ = requests.get(redirect, cookies=cookies, verify=False)

    if cookies:
        return cookies['session_cookie']
    return ''


def from_session(cookie: str):
    response = requests.get(f'{_URL}/user', cookies={
        'session_cookie': cookie
    }, verify=False)
    print(response.content.decode('utf-8'))


if __name__ == '__main__':
    print('Checking server status...')
    if not is_alive():
        print('Server down, exiting')
        sys.exit(1)

    print('Logging in...')
    cookie = do_login()
    print('Check whether logged in...')
    from_session(cookie)

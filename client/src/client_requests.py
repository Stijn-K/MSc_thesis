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
    response = requests.post(f'{_URL}/login', data={
        'username': 'test_user',
        'password': '12345'
    }, verify=False)
    return response.cookies['session_cookie']


def get_user(cookie: str) -> Optional[dict]:
    response = requests.get(f'{_URL}/user', cookies={
        'session_cookie': cookie
    }, verify=False)
    if response.status_code == 200:
        return response.json()
    return None


if __name__ == '__main__':
    print('Checking server status...')
    if not is_alive():
        print('Server down, exiting')
        sys.exit(1)

    print('Logging in...')
    cookie = do_login()
    print('Check whether logged in...')
    user = get_user(cookie)
    if user:
        print(f"Successfully fetched userdata with cookie: \n {user}")
    else:
        print('Failed to fetch userdata with cookie')

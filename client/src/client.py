import os
import sys
from typing import Optional

from requests.cookies import CookieConflictError
from requests_html import HTMLSession

from dotenv import load_dotenv

import warnings
from urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)

load_dotenv()

_SERVER = os.getenv('SERVER')
_URL = f'https://{_SERVER}:5000'


def get_url(endpoint: str, query: dict = None) -> str:
    url = f'{_URL}/{endpoint}'
    if query:
        query = '&'.join([f'{k}={v}' for k, v in query.items()])
        url += f'?{query}'
    return url


def is_alive(session: HTMLSession) -> bool:
    try:
        r = session.get(get_url('alive'))
        return r.status_code == 204
    except ConnectionError:
        return False


def do_login(session: HTMLSession) -> Optional[str]:
    r = session.post(get_url('login'), data={'username': 'test_user', 'password': '12345'})
    if r.status_code == 401:
        return None
    return session.cookies.get('session_cookie')


def from_session(session: HTMLSession, cookie: str) -> None:
    try:
        if not session.cookies.get('session_cookie'):
            session.cookies.set(name='session_cookie', value=cookie, domain=_SERVER)
    except CookieConflictError:
        pass

    page = session.get(get_url('user'))

    scripts = [x.attrs['src'] for x in page.html.find('script')]
    for script in scripts:
        js = session.get(get_url(script.lstrip('/'))).content.decode('utf-8')
        page.html.render(script=js, reload=False)

    print(page.html.html)


if __name__ == '__main__':
    session = HTMLSession(verify=False)
    print('Checking server status...')
    if not is_alive(session):
        print('Server down, exiting')
        session.close()
        sys.exit(1)

    print('Logging in...')
    cookie = do_login(session)
    if not cookie:
        print('Invalid login, exiting')
        session.close()
        sys.exit(1)

    print('Check whether logged in...')
    from_session(session, cookie)
    session.close()

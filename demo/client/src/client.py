import os
import sys
import time

import hashlib
import hmac

from seleniumwire import webdriver
from seleniumwire.request import Request, Response

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from dotenv import load_dotenv

load_dotenv()

_DRIVER_PATH = os.getenv('CHROMEDRIVER')
_SERVER = os.getenv('SERVER')
_URL = f'https://{_SERVER}:5000'

_OTC = {
    # set by client
    'v': '1.0',             # OTC version
    'uid': 'test_user',     # user ID / username
    'pwd': '12345',         # password
    'expiration': 60,       # token expiration time (60 seconds)

    # set by server
    'ticket': None,         # ticket
    'cid': None,            # OTC credential's ID
    'k_s': None,            # session key
    'n_s': None,            # session nonce
    't_s': 0,               # session expiration time
    'domain': None,         # OTC credential's scope
    'path': None,           # OTC credential's scope
}


def otc_request_interceptor(request: Request) -> None:
    global _OTC
    if not _OTC['ticket']:
        request.headers['X-OTC'] = _OTC['v']
        return

    t_h = int(time.time()) + _OTC['expiration']
    msg = f'{request.url}|{t_h}|{request.body.hex()}'.encode()
    h = hmac.new(bytes.fromhex(_OTC['k_s']), msg, hashlib.sha256).hexdigest()
    request.headers['X-OTC'] = f'{_OTC["cid"]},{_OTC["n_s"]},{t_h},{h},{_OTC["ticket"]}'


def otc_response_interceptor(request: Request, response: Response) -> None:
    if request.method == 'POST' and request.path == '/login':
        otc_values = response.headers['X-OTC-SET'].split(',')
        _OTC['cid'] = otc_values[0]
        _OTC['domain'] = otc_values[1]
        _OTC['path'] = otc_values[2]
        _OTC['n_s'] = otc_values[3]
        _OTC['k_s'] = otc_values[4]
        _OTC['t_s'] = otc_values[5]
        _OTC['ticket'] = otc_values[6]


def get_url(endpoint: str, **params) -> str:
    url = f'{_URL}/{endpoint}'
    query = '&'.join([f'{k}={v}' for k, v in params.items()])
    if query:
        url += f'?{query}'
    return url


def is_alive(driver: WebDriver) -> bool:
    try:
        driver.get(get_url('alive'))
        return True
    except WebDriverException:
        return False


def do_login(driver: WebDriver) -> tuple[bool, str]:
    driver.get(get_url('login'))
    username = driver.find_element(By.ID, 'username')
    username.clear()
    username.send_keys(_OTC['uid'])

    password = driver.find_element(By.ID, 'password')
    password.clear()
    password.send_keys(_OTC['pwd'])

    driver.find_element(By.ID, 'submit').click()

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'header')))

    if driver.find_elements(By.ID, 'user'):
        return True, 'show ticket or something here'

    elif elem := driver.find_elements(By.ID, 'error'):
        return False, elem[0].text

    return False, 'Unexpected error'


def from_session(driver: WebDriver, cookie: str):
    driver.get(get_url('user'))

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'header')))

    print(driver.page_source)


if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.add_argument('ignore-certificate-errors')
    # options.add_argument('--headless')
    driver = webdriver.Chrome(service=ChromeService(executable_path=_DRIVER_PATH), options=options)
    driver.request_interceptor = otc_request_interceptor
    driver.response_interceptor = otc_response_interceptor

    print('Checking server status...')
    if not is_alive(driver):
        print('Server down, exiting')
        driver.close()
        sys.exit(1)

    print('Logging in...')
    success, result = do_login(driver)
    if not success:
        print(f'Failed to log in: {result}')
        driver.close()
        sys.exit(1)

    print(f'Logged in, cookie: {result}')
    print('Fetching user page for timing...')
    from_session(driver, result)

    # driver.close()

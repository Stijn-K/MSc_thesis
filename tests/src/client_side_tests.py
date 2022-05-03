import os
import time
import sys
import json

import hashlib
import hmac

from seleniumwire import webdriver
from seleniumwire.request import Request, Response

from selenium.common.exceptions import WebDriverException, TimeoutException
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

_RESULTS_PATH = os.getenv('RESULTS')
_BRANCH = os.getenv('BRANCH')

timings = {
    'login': {
        'frontend': [],
        'backend': [],
        'server': {
            'GET': [],
            'POST': [],
        }
    },
    'user': {
        'frontend': [],
        'backend': [],
        'server': {
            'GET': [],
            'POST': [],
        }
    },
}

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

    if not (request.path.endswith('.js') or request.path == '/alive'):
        total_time = round(float(response.headers['request_time']) / 1_000_000, 2)
        timings[request.path[1:]]['server'][request.method].append(total_time)


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


def time_login(driver: WebDriver) -> None:
    driver.get(get_url('login'))
    username = driver.find_element(By.ID, 'username')
    username.clear()
    username.send_keys('test_user')

    password = driver.find_element(By.ID, 'password')
    password.clear()
    password.send_keys('12345')

    driver.find_element(By.ID, 'submit').click()

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'logged_in')))
    except TimeoutException:
        print('Login failed')
        return

    navigation_start = driver.execute_script("return window.performance.timing.navigationStart")
    response_start = driver.execute_script("return window.performance.timing.responseStart")
    dom_complete = driver.execute_script("return window.performance.timing.domComplete")

    backend_performance = response_start - navigation_start
    frontend_performance = dom_complete - response_start

    timings['login']['frontend'].append(frontend_performance)
    timings['login']['backend'].append(backend_performance)


def time_user(driver: WebDriver) -> None:
    driver.get(get_url('user'))
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'header')))

    if elem := driver.find_elements(By.ID, 'error'):
        print(f'Error: {elem[0].text}')
        return

    navigation_start = driver.execute_script("return window.performance.timing.navigationStart")
    response_start = driver.execute_script("return window.performance.timing.responseStart")
    dom_complete = driver.execute_script("return window.performance.timing.domComplete")

    backend_performance = response_start - navigation_start
    frontend_performance = dom_complete - response_start

    timings['user']['frontend'].append(frontend_performance)
    timings['user']['backend'].append(backend_performance)


def write_to_file(data):
    with open(f'{_RESULTS_PATH}timings-{_BRANCH}.json', 'w+') as f:
        f.write(json.dumps(data))


if __name__ == '__main__':
    num_tests = 110

    options = webdriver.ChromeOptions()
    # ignore errors caused by self-signed certificates
    options.add_argument('--ignore-certificate-errors')
    # disable web security protocols (prevent CORS errors)
    options.add_argument('--disable-web-security')
    # disable chrome's built-in network cache
    options.add_argument('--disk-cache-size 0')
    # run browser in headless mode
    options.add_argument('--headless')

    wire_options = {
        'request_storage': 'memory',
        'request_storage_max_size': 5
    }

    driver = webdriver.Chrome(service=ChromeService(executable_path=_DRIVER_PATH),
                              options=options,
                              seleniumwire_options=wire_options
                              )

    driver.response_interceptor = otc_response_interceptor
    driver.request_interceptor = otc_request_interceptor

    if not is_alive(driver):
        print('Server down, exiting')
        driver.quit()
        sys.exit(1)

    for i in range(num_tests):
        print(i)
        driver.delete_all_cookies()
        time_login(driver)
        time_user(driver)
        time.sleep(.5)

    driver.quit()

    print(timings)
    write_to_file(timings)

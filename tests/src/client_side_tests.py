import os
import time
import sys

from seleniumwire import webdriver
from seleniumwire.request import Request, Response

from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import json
import numpy as np

from dotenv import load_dotenv

load_dotenv()

_DRIVER_PATH = os.getenv('CHROMEDRIVER')
_SERVER = os.getenv('SERVER')
_URL = f'https://{_SERVER}:5000'

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


# grab response time from response headers
# time is returned in nanoseconds and converted to milliseconds
def timing_response_interceptor(request: Request, response: Response) -> None:
    if request.path.endswith('.js') \
            or request.path.endswith('.ico') \
            or request.path == '/alive':
        return

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


if __name__ == '__main__':
    num_tests = 5

    np.random.seed(0)
    _NUM_PUFS = 5
    _PUFS = [list(np.random.normal(size=10)) for _ in range(_NUM_PUFS)]
    _PUF_ORDER = list(range(1, _NUM_PUFS + 1))

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

    driver.response_interceptor = timing_response_interceptor

    if not is_alive(driver):
        print('Server down, exiting')
        driver.quit()
        sys.exit(1)

    driver.execute_script(f'window.localStorage.setItem("pufs","{json.dumps(_PUFS)}");')
    driver.execute_script(f'window.localStorage.setItem("order","{json.dumps(_PUF_ORDER)}");')

    for i in range(num_tests):
        print(i)
        driver.delete_all_cookies()
        time_login(driver)
        time_user(driver)
        time.sleep(.5)

    driver.quit()

    print(timings)
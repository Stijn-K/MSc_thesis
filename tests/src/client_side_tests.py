import os
import time
import sys
import json

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

_RESULTS_PATH = os.getenv('RESULTS')
_BRANCH = os.getenv('BRANCH')

timings = {
    'login': {
        'get_page': [],
        'post_login': [],
        'server': {
            'GET': [],
            'POST': [],
        }
    },
    'user': {
        'get_page': [],
        'fetch_data': [],
        'server': {
            'GET': [],
            'POST': [],
        }
    },
}


# grab response time from response headers
# time is returned in nanoseconds and converted to milliseconds
def timing_response_interceptor(request: Request, response: Response) -> None:
    if request.path.endswith('.js') or request.path == '/alive':
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

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'logged_in')))

    navigation_start: int = driver.execute_script("return window.performance.timing.navigationStart")
    dom_complete: int = driver.execute_script("return window.performance.timing.domComplete")

    timer: dict[str, int] = driver.execute_script('return timer')

    get_page_time = dom_complete - navigation_start
    post_login = timer['t1'] - timer['t0']

    timings['login']['get_page'].append(get_page_time)
    timings['login']['post_login'].append(post_login)


def time_user(driver: WebDriver) -> None:
    driver.get(get_url('user'))
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'header')))

    if elem := driver.find_elements(By.ID, 'error'):
        print(f'Error: {elem[0].text}')
        return

    navigation_start: int = driver.execute_script("return window.performance.timing.navigationStart")
    dom_complete: int = driver.execute_script("return window.performance.timing.domComplete")

    get_page_time = dom_complete - navigation_start

    timings['user']['get_page'].append(get_page_time)
    timings['user']['fetch_data'].append(-1)


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

    driver.response_interceptor = timing_response_interceptor

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

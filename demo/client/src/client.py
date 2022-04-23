import os
import sys

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
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

np.random.seed(0)
_NUM_PUFS = 5
_PUFS = [list(np.random.normal(size=10)) for _ in range(_NUM_PUFS)]
_PUF_ORDER = list(range(1, _NUM_PUFS+1))


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
    username.send_keys('test_user')

    password = driver.find_element(By.ID, 'password')
    password.clear()
    password.send_keys('12345')

    driver.find_element(By.ID, 'submit').click()

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'header')))

    if driver.find_elements(By.ID, 'logged_in'):
        return True, driver.get_cookie('session_cookie')['value']

    elif elem := driver.find_elements(By.ID, 'error'):
        return False, elem[0].text

    return False, 'Unexpected error'


def from_session(driver: WebDriver, cookie: str):
    driver.delete_all_cookies()
    driver.add_cookie({'name': 'session_cookie', 'value': cookie})
    driver.get(get_url('user'))

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'header')))

    print(driver.page_source)


if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.add_argument('ignore-certificate-errors')
    # options.add_argument('--headless')
    driver = webdriver.Chrome(service=ChromeService(executable_path=_DRIVER_PATH), options=options)

    print('Checking server status...')
    if not is_alive(driver):
        print('Server down, exiting')
        driver.quit()
        sys.exit(1)

    driver.execute_script(f'window.localStorage.setItem("pufs","{json.dumps(_PUFS)}");')
    driver.execute_script(f'window.localStorage.setItem("order","{json.dumps(_PUF_ORDER)}");')

    print('Logging in...')
    success, result = do_login(driver)
    if not success:
        print(f'Failed to log in: {result}')
        driver.quit()
        sys.exit(1)

    print(f'Logged in, cookie: {result}')
    print('Fetching user page for timing...')
    from_session(driver, result)

    # driver.quit()

import os
import sys

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver

from dotenv import load_dotenv

load_dotenv()

_DRIVER_PATH = os.getenv('CHROMEDRIVER')
_SERVER = os.getenv('SERVER')
_URL = f'https://{_SERVER}:5000'


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


def from_session(driver: WebDriver, cookie: str):
    driver.delete_all_cookies()
    driver.add_cookie({'name': 'session_cookie', 'value': cookie})
    driver.get(get_url('user'))
    print(driver.page_source)


if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.add_argument('ignore-certificate-errors')
    # options.add_argument('--headless')
    driver = webdriver.Chrome(service=ChromeService(executable_path=_DRIVER_PATH), options=options)

    print('Checking server status...')
    if not is_alive(driver):
        print('Server down, exiting')
        driver.close()
        sys.exit(1)

    print('Magically fetching cookie...')
    cookie = 'this_is_a_session_cookie'

    print('Check whether logged in...')
    from_session(driver, cookie)

    # driver.close()

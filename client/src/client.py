import os
import sys

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver

from dotenv import load_dotenv
from selenium.webdriver.common.by import By

load_dotenv()

driver_path = os.getenv('CHROMEDRIVER')

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


def do_login(driver: WebDriver) -> str:
    driver.get(get_url('login'))
    username = driver.find_element(By.ID, 'username')
    username.clear()
    username.send_keys('test_user')

    password = driver.find_element(By.ID, 'password')
    password.clear()
    password.send_keys('12345')

    driver.find_element(By.ID, 'submit').click()

    return driver.get_cookie('session_cookie')['value']


def from_session(driver: WebDriver, cookie: str):
    driver.delete_all_cookies()
    driver.add_cookie({'name': 'session_cookie', 'value': cookie})
    driver.get(get_url('user'))
    print(driver.page_source)


if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.add_argument('ignore-certificate-errors')
    # options.add_argument('--headless')
    driver = webdriver.Chrome(service=ChromeService(executable_path=driver_path), options=options)

    print('Checking server status...')
    if not is_alive(driver):
        print('Server down, exiting')
        driver.close()
        sys.exit(1)

    print('Logging in...')
    cookie = do_login(driver)
    print(f'Got cookie: {cookie}')
    print('Check whether logged in...')
    from_session(driver, cookie)

    # driver.close()

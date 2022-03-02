from __future__ import annotations

import os
import sys
from dotenv import load_dotenv

from locust import FastHttpUser, task, constant_throughput
from http.cookiejar import Cookie

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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


def do_login(driver: WebDriver) -> tuple[bool, str|dict]:
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
        return True, driver.get_cookie('session_cookie')

    elif elem := driver.find_elements(By.ID, 'error'):
        return False, elem[0].text

    return False, 'Unexpected error'


options = webdriver.ChromeOptions()
options.add_argument('ignore-certificate-errors')
options.add_argument('--headless')
driver = webdriver.Chrome(service=ChromeService(executable_path=_DRIVER_PATH), options=options)

success, content = do_login(driver)
driver.quit()
if not success:
    sys.exit(1)

cookie = Cookie(1, content['name'], content['value'], None, None, content['domain'], None, None, content['path'], None, False, False, None, None, None, None)


class TestUser(FastHttpUser):
    wait_time = constant_throughput(1)

    @task
    def user(self):
        self.client.cookiejar.set_cookie(cookie)
        self.client.get('/user', verify=False)

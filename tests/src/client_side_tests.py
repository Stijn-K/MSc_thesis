import os
import time

from selenium import webdriver
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


def get_url(endpoint: str, **params) -> str:
    url = f'{_URL}/{endpoint}'
    query = '&'.join([f'{k}={v}' for k, v in params.items()])
    if query:
        url += f'?{query}'
    return url


def time_login(driver: WebDriver) -> tuple[int, int]:
    driver.get(get_url('login'))
    username = driver.find_element(By.ID, 'username')
    username.clear()
    username.send_keys('test_user')

    password = driver.find_element(By.ID, 'password')
    password.clear()
    password.send_keys('12345')

    driver.find_element(By.ID, 'submit').click()

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'header')))

    navigation_start = driver.execute_script("return window.performance.timing.navigationStart")
    response_start = driver.execute_script("return window.performance.timing.responseStart")
    dom_complete = driver.execute_script("return window.performance.timing.domComplete")

    backend_performance = response_start - navigation_start
    frontend_performance = dom_complete - response_start

    return backend_performance, frontend_performance


def time_user(driver: WebDriver) -> tuple[int, int]:
    driver.get(get_url('user'))
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'header')))

    if elem := driver.find_elements(By.ID, 'error'):
        print(elem[0].text)

    navigation_start = driver.execute_script("return window.performance.timing.navigationStart")
    response_start = driver.execute_script("return window.performance.timing.responseStart")
    dom_complete = driver.execute_script("return window.performance.timing.domComplete")

    backend_performance = response_start - navigation_start
    frontend_performance = dom_complete - response_start

    return backend_performance, frontend_performance

if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.add_argument('ignore-certificate-errors')
    options.add_argument('--disk-cache-size 0')
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=ChromeService(executable_path=_DRIVER_PATH), options=options)

    timings = {
        'login': {
            'frontend': [],
            'backend': []
        },
        'user': {
            'frontend': [],
            'backend': []
        },

    }

    for i in range(100):
        print(i)
        b, f = time_login(driver)
        timings['login']['frontend'].append(f)
        timings['login']['backend'].append(b)

        b, f = time_user(driver)
        timings['user']['frontend'].append(f)
        timings['user']['backend'].append(b)

        time.sleep(.5)

    driver.quit()

    print(timings)

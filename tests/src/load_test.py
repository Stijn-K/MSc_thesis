from __future__ import annotations

import os

from locust import FastHttpUser, task, constant_throughput

from dotenv import load_dotenv

load_dotenv()

_DRIVER_PATH = os.getenv('CHROMEDRIVER')
_SERVER = os.getenv('SERVER')
_URL = f'https://{_SERVER}:5000'


class TestUser(FastHttpUser):
    wait_time = constant_throughput(1)

    def on_start(self):
        self.client.post(f'{_URL}/login', json={'username': 'test_user', 'password': '12345'}, verify=False)

    @task(1)
    def user(self):
        self.client.get(f'{_URL}/user', verify=False)

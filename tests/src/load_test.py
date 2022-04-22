from __future__ import annotations

import os
import re

from locust import FastHttpUser, task, constant_throughput

from dotenv import load_dotenv

load_dotenv()

_SERVER = os.getenv('SERVER')
_URL = f'https://{_SERVER}:5000'
_ERROR_RE = re.compile(r'<h2 id="error">Error: (.*?)<\/h2>', re.DOTALL)


class TestUser(FastHttpUser):
    wait_time = constant_throughput(1)

    data = {
        'username': 'test_user',
        'password': '12345'
    }

    def on_start(self):
        self.client.post(f'{_URL}/login', json=self.data)

    @task(1)
    def user(self):
        with self.client.get(f'{_URL}/user') as response:
            if error := _ERROR_RE.search(response.text):
                response.failure(error.group(1))

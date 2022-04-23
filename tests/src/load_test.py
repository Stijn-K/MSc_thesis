from __future__ import annotations

import os
import re

from contextlib import contextmanager
import warnings
import urllib3

from locust import FastHttpUser, task, constant_throughput, HttpUser

from dotenv import load_dotenv

load_dotenv()

_SERVER = os.getenv('SERVER')
_URL = f'https://{_SERVER}:5000'
_CLIENT_CERT = os.getenv('CLIENT_CERT')

_ERROR_RE = re.compile(r'<h2 id="error">Error: (.*?)<\/h2>', re.DOTALL)


@contextmanager
def disable_ssl_warnings():
    with warnings.catch_warnings():
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        yield None


class TestUser(HttpUser):
    wait_time = constant_throughput(1)

    data = {
        'username': 'test_user',
        'password': '12345',
    }

    def on_start(self):
        with disable_ssl_warnings():
            self.client.post(f'{_URL}/login', json=self.data, verify=False, cert=_CLIENT_CERT)

    @task(1)
    def user(self):
        with disable_ssl_warnings():
            with self.client.get(f'{_URL}/user', cert=_CLIENT_CERT, verify=False, catch_response=True) as response:
                if error := _ERROR_RE.search(response.text):
                    response.failure(error.group(1))

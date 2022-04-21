from __future__ import annotations

import os
import ast

import re
challenges_re = re.compile(r'challenges = (\[.*?\])', re.DOTALL | re.MULTILINE)

from locust import FastHttpUser, task, constant_throughput

from dotenv import load_dotenv

load_dotenv()

_SERVER = os.getenv('SERVER')
_URL = f'https://{_SERVER}:5000'


class TestUser(FastHttpUser):
    wait_time = constant_throughput(1)

    data = {
        'username': 'test_user',
        'password': '12345',
        'challenges': {

        }
    }

    def on_start(self):
        with self.client.get(f'{_URL}/login', verify=False) as response:
            for challenge in ast.literal_eval(challenges_re.search(response.text).group(1)):
                self.data['challenges'][challenge] = '11111'
        self.client.post(f'{_URL}/login', json=self.data, verify=False)

    @task(1)
    def user(self):
        with self.client.get(f'{_URL}/user', verify=False) as response:
            for challenge in ast.literal_eval(challenges_re.search(response.text).group(1)):
                self.data['challenges'][challenge] = '11111'

        self.client.post(f'{_URL}/user', json=self.data, verify=False)

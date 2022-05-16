from __future__ import annotations

import os
import ast

import re

from locust import FastHttpUser, task, constant_throughput, SequentialTaskSet
from locust_plugins.transaction_manager import TransactionManager

from dotenv import load_dotenv

load_dotenv()

_SERVER = os.getenv('SERVER')
_URL = f'https://{_SERVER}:5000'

challenges_re = re.compile(r'challenges = (\[.*?\])', re.DOTALL | re.MULTILINE)


class TestUserTaskSet(SequentialTaskSet):
    host = _URL
    wait_time = constant_throughput(1)

    data = {
        'username': 'test_user',
        'password': '12345',
        'challenges': {

        }
    }

    tm = None

    def on_start(self):
        with self.client.get(f'{_URL}/login') as response:
            for challenge in ast.literal_eval(challenges_re.search(response.text).group(1)):
                self.data['challenges'][challenge] = '11111'
        self.client.post(f'{_URL}/login', json=self.data)

        self.tm = TransactionManager()

    @task
    def get_user(self):
        self.tm.start_transaction('user')
        with self.client.get(f'{_URL}/user') as response:
            for challenge in ast.literal_eval(challenges_re.search(response.text).group(1)):
                self.data['challenges'][challenge] = '11111'

    @task
    def post_user(self):
        self.client.post(f'{_URL}/user', json=self.data)
        self.tm.end_transaction('user')


class TestUserTransaction(FastHttpUser):
    tasks = [TestUserTaskSet]

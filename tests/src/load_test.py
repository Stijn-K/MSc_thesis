from __future__ import annotations

import os

from locust import FastHttpUser, task, constant_throughput, SequentialTaskSet
from locust_plugins.transaction_manager import TransactionManager

from dotenv import load_dotenv

load_dotenv()

_SERVER = os.getenv('SERVER')
_URL = f'https://{_SERVER}:5000'


class TestUserTaskSet(SequentialTaskSet):
    wait_time = constant_throughput(1)

    data = {
        'username': 'test_user',
        'password': '12345',
        'fingerprint': {
            'audio': '1',
            'canvas': '1'
        }
    }

    tm = None

    def on_start(self):
        self.client.post(f'{_URL}/login', json=self.data)
        self.tm = TransactionManager()

    @task
    def get_user(self):
        self.tm.start_transaction('user')
        self.client.get(f'{_URL}/user')

    @task
    def post_user(self):
        self.client.post(f'{_URL}/user', json=self.data)
        self.tm.end_transaction('user')


class TestUserTransaction(FastHttpUser):
    tasks = [TestUserTaskSet]

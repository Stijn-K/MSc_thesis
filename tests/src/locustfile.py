import os
from dotenv import load_dotenv

from locust import HttpUser, task, constant_throughput, events


load_dotenv()
_SERVER = os.getenv('SERVER')
_URL = f'https://{_SERVER}:5000'


class TestUser(HttpUser):
    wait_time = constant_throughput(1)

    def on_start(self):
        self.client.post('/login', {
            'username': 'test_user',
            'password': '12345'
        }, verify=False)

    @task
    def user(self):
        self.client.get('/user', verify=False)

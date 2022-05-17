from __future__ import annotations

import os
import ast

import re

import gevent
from locust import FastHttpUser, task, constant_throughput, SequentialTaskSet
from locust.env import Environment
from locust.stats import stats_history, StatsCSVFileWriter
from locust_plugins.transaction_manager import TransactionManager

from dotenv import load_dotenv

load_dotenv()

_SERVER = os.getenv('SERVER')
_RESULTS = os.getenv("RESULTS")
_BRANCH = os.getenv("BRANCH")
_URL = f'https://{_SERVER}:5000'

_ERROR_RE = re.compile(r'<h2 id="error">Error: (.*?)</h2>', re.DOTALL)

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
    host = _URL
    tasks = [TestUserTaskSet]


def start_locust(users: int, spawn_rate: int, time_min: int) -> None:
    # Setup Environment and Runner
    env = Environment(user_classes=[TestUserTransaction])
    env.create_local_runner()

    # CSV Writer
    stats_path = os.path.join(_RESULTS, 'load_tests', _BRANCH, f'{users}')
    csv_writer = StatsCSVFileWriter(
        environment=env,
        base_filepath=stats_path,
        full_history=False,
        percentiles_to_report=[0.50, 0.95]
    )

    # Start test
    env.runner.start(users, spawn_rate)

    # start a greenlet to save stats to history
    gevent.spawn(stats_history, env.runner)

    # stop the runner after time_min minutes
    gevent.spawn_later(time_min * 60, lambda: env.runner.quit())

    # start a greenlet to write stats to csv
    gevent.spawn(csv_writer.stats_writer)

    # wait for all greenlets to finish
    env.runner.greenlet.join()


if __name__ == '__main__':
    # tests = [(5, 1, 1), (10, 2, 1), (20, 5, 1), (50, 10, 1), (100, 20, 1)]
    tests = [(1,1,1)]
    num_tests = len(tests)
    for num, (users, spawn_rate, time_min) in enumerate(tests, 1):
        print(f'{num}/{num_tests}: Running test with {users} users, {spawn_rate} spawn rate, {time_min} minutes')
        start_locust(users, spawn_rate, time_min)
        print(f'Test finished')

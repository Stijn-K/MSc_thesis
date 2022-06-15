from __future__ import annotations

import os
import glob

import gevent
import locust
from locust import FastHttpUser, task, constant_throughput
from locust.env import Environment
from locust.stats import stats_history, StatsCSVFileWriter
from locust_plugins.transaction_manager import TransactionManager

from dotenv import load_dotenv

load_dotenv()

_SERVER = os.getenv('SERVER')
_RESULTS = os.getenv("RESULTS")
_BRANCH = os.getenv("BRANCH")
_URL = f'https://{_SERVER}:5000'


class TestUser(FastHttpUser):
    host = _URL

    number_of_clients = 0

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

        TransactionManager.transactions_filename = os.path.join(_RESULTS, 'load_tests', _BRANCH, f'{self.number_of_clients}_transactions.csv')
        TransactionManager.transactions_summary_filename = os.path.join(_RESULTS, 'load_tests', _BRANCH, f'{self.number_of_clients}_transactions_summary.csv')
        TransactionManager.log_transactions_in_file = True
        TransactionManager._create_results_log()

        self.tm = TransactionManager()

    @task
    def user(self):
        self.tm.start_transaction('user')
        self.client.get(f'{_URL}/user')
        self.client.post(f'{_URL}/user', json=self.data)
        self.tm.end_transaction('user')


def start_locust(users: int, spawn_rate: int, time_min: int, stats_path: str) -> None:
    # Setup Environment and Runner
    TestUser.number_of_clients = users
    env = Environment(user_classes=[TestUser])
    env.create_local_runner()

    locust.events.init.fire(environment=env, runner=env.runner)

    # CSV Writer
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

    locust.events.test_stop.fire()


if __name__ == '__main__':
    tests = [(10, 5, 1), (20, 5, 1), (40, 10, 1), (80, 10, 1), (160, 20, 1)]
    num_tests = len(tests)

    path = os.path.join(_RESULTS, 'load_tests', _BRANCH)
    for f in glob.glob(path + '/*'):
        os.remove(f)

    for num, (users, spawn_rate, time_min) in enumerate(tests, 1):
        print(f'{num}/{num_tests}: Running test with {users} users, {spawn_rate} spawn rate, {time_min} minutes')
        stats_path = os.path.join(path, str(users))
        start_locust(users, spawn_rate, time_min, stats_path)
        print(f'Test finished')

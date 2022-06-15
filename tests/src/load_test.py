from __future__ import annotations

import os
import re
import glob

import time
import hashlib
import hmac

import gevent
from locust import FastHttpUser, task, constant_throughput
from locust.env import Environment
from locust.stats import stats_history, StatsCSVFileWriter

from dotenv import load_dotenv

load_dotenv()

_SERVER = os.getenv('SERVER')
_URL = f'https://{_SERVER}:5000'
_RESULTS = os.getenv("RESULTS")
_BRANCH = os.getenv("BRANCH")
_ERROR_RE = re.compile(r'<h2 id="error">Error: (.*?)<\/h2>', re.DOTALL)


class TestUser(FastHttpUser):
    host = _URL

    _OTC = {
        # set by client
        'v': '1.0',  # OTC version
        'uid': 'test_user',  # user ID / username
        'pwd': '12345',  # password
        'expiration': 60,  # token expiration time (60 seconds)

        # set by server
        'ticket': None,  # ticket
        'cid': None,  # OTC credential's ID
        'k_s': None,  # session key
        'n_s': None,  # session nonce
        't_s': 0,  # session expiration time
        'domain': None,  # OTC credential's scope
        'path': None,  # OTC credential's scope
    }

    data = {
        'username': 'test_user',
        'password': '12345',
    }

    def on_start(self):
        with self.client.post(f'{_URL}/login', json=self.data) as response:
            otc_values = response.headers['X-OTC-SET'].split(',')
            self._OTC['cid'] = otc_values[0]
            self._OTC['domain'] = otc_values[1]
            self._OTC['path'] = otc_values[2]
            self._OTC['n_s'] = otc_values[3]
            self._OTC['k_s'] = otc_values[4]
            self._OTC['t_s'] = otc_values[5]
            self._OTC['ticket'] = otc_values[6]

    @task(1)
    def user(self):
        t_h = int(time.time()) + self._OTC['expiration']
        body = ''
        msg = f'{_URL}/user|{t_h}|{body}'.encode()

        h = hmac.new(bytes.fromhex(self._OTC['k_s']), msg, hashlib.sha256).hexdigest()
        otc_header = f'{self._OTC["cid"]},{self._OTC["n_s"]},{t_h},{h},{self._OTC["ticket"]}'

        with self.client.get(f'{_URL}/user', headers={'X-OTC': otc_header}, catch_response=True) as response:
            if error := _ERROR_RE.search(response.text):
                response.failure(error.group(1))


def start_locust(users: int, spawn_rate: int, time_min: int, stats_path: str) -> None:
    # Setup Environment and Runner
    env = Environment(user_classes=[TestUser])
    env.create_local_runner()

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

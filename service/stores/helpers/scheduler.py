import argparse
import os.path
import time

# from crontab import CronTab

from .common import _log
from .common import _err
from .common import _exc
from .common import uwsgi_lock

from .api import OzonApi
from ..models import StoreWarehouse


def parse_args():
    try:
        parser = argparse.ArgumentParser(description='username for ozon stock update job')
        parser.add_argument('username', type=str, help='username')
        args = parser.parse_args()
        _username = args.username
        _log(f'parsed username passed to script: {username}')
        return _username
    except Exception as err:
        err_msg = f'failed to parse "username" arg: {_exc(err)}'
        _err(err_msg)


class Worker:
    sys_user = 'dockeruser'

    # noinspection PyUnresolvedReferences
    @staticmethod
    def update_ozon_stocks(_username):
        if not _username:
            _log('username is None or an empty string')
            return

        whs = StoreWarehouse.objects.filter(user__username=_username)
        if not len(whs):
            _log(f'no store whs found for username "{_username}"')
            return

        for wh in whs:
            if not wh.stock_update_available():
                _log(f'store wh "{wh.name}" skipped, stock update not supported by marketplace')
                continue

            if not wh.store.is_active():
                _log(f'store wh "{wh.name}" skipped, stock update not supported by marketplace')
                continue

            # err = OzonApi().update_stock(wh)
            err = OzonApi().fake_update_stock(wh)
            if err:
                _err(err)

            # todo - log to job execution log

    # @uwsgi_lock
    def _start_jobs(self):
        _log('(scheduler) starting jobs ...')

        duration = 20
        current = 0

        schedule = {
            'test 1': 3,
            'test 2': 5,
            'test 3': 10,
        }

        while current <= duration:
            for k, v in schedule.items():
                if current > 0 and not current % v:
                    _log(f'{k}: must be called every {v} secs (current: {current})')
            _log('sleeping 1 sec...')
            current += 1
            time.sleep(1)

    # @uwsgi_lock
    def start_jobs(self):
        lock_filename = 'lock.file'
        if os.path.exists(lock_filename):
            return
        try:
            with open(lock_filename, 'w') as file:
                file.write(f'{lock_filename}')
                self._start_jobs()
        except (OSError, Exception) as err:
            err_msg = f'failed to create lock file "{lock_filename}": {_exc(err)}'
            _err(err_msg)


if __name__ == '__main__':
    username = parse_args()
    Worker.update_ozon_stocks(username)

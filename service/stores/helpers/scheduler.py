import argparse
import os.path

# from crontab import CronTab

from .common import _log
from .common import _err
from .common import _exc
# from .common import uwsgi_lock

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
        schedule = {
            'admin': 20,
            'test': 20,
        }
        for k, v in schedule.items():
            pass

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

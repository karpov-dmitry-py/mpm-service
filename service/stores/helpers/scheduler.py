import os.path
from crontab import CronTab

from .common import _log
from .common import _err
from .common import _exc
from .common import time_tracker
from .api import OzonApi
from ..models import StoreWarehouse


class Scheduler:
    update_stock_pattern = 'update stock'

    os_user = 'dockeruser'
    # os_user = 'dkarpov'

    intepreter_path = '/usr/local/bin/python3'
    # intepreter_path = '/home/dkarpov/projects/self/mpm-service/venv/bin/python'

    command_path = '/home/dockeruser/workdir/manage.py scheduler'
    # command_path = '/home/dkarpov/projects/self/mpm-service/service/manage.py scheduler'

    # cron_log_path = '/home/dkarpov/projects/self/mpm-service/service/stores/cron.log'
    cron_log_path = '/home/dockeruser/workdir/cron.log'

    # noinspection PyUnresolvedReferences
    @staticmethod
    @time_tracker('(scheduler) update_ozon_stocks')
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
                _log(f'store wh "{wh.name}" skipped, store "{wh.store.name}" is inactive')
                continue

            # err = OzonApi().update_stock(wh)
            err = OzonApi().fake_update_stock(wh)
            if err:
                _err(err)

            # todo - log to job execution log

    # @uwsgi_lock
    def _add_jobs(self):
        _log('(scheduler) adding jobs to cron ...')

        user = self.os_user
        app_users = ("admin",)  # todo - fetch schedule from db

        self._drop_jobs(user)
        cron = CronTab(user=user)

        for app_user in app_users:
            command_args = app_user
            job = cron.new(command=f'{self.intepreter_path} {self.command_path} {command_args} '
                                   f'>> {self.cron_log_path} 2>&1', comment=f'{self.update_stock_pattern}: {app_user}')
            job.minute.every(1)
            cron.write()
            _log(f'added a cron job for app user: {app_user}')

    def run_scheduler(self):
        lock_filename = 'lock.file'
        if os.path.exists(lock_filename):
            return

        try:
            with open(lock_filename, 'w') as file:
                file.write(lock_filename)
                os.system('service cron start')
        except (OSError, Exception) as err:
            err_msg = f'failed to run scheduler: {_exc(err)}'
            _err(err_msg)
            return

        self._add_jobs()

    def _drop_jobs(self, os_user):
        cron = CronTab(user=os_user)
        for job in cron:
            if self.update_stock_pattern in job.comment:
                _log(f'removing update stock cron job: {job.comment}')
                cron.remove(job)
                cron.write()

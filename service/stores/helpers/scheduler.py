import os.path
from crontab import CronTab

from .common import _log
from .common import _err
from .common import _exc
from .common import time_tracker
from .api import OzonApi
from ..models import StoreWarehouse


class Scheduler:
    mode = 'dev'
    # mode = 'prod'
    update_stock_pattern = 'update stock'
    settings = {
        'dev': {
            'os_user': 'dkarpov',
            'intepreter_path': '/home/dkarpov/projects/self/mpm-service/venv/bin/python',
            'command_path': '/home/dkarpov/projects/self/mpm-service/service/manage.py scheduler',
            'cron_log_path': '/home/dkarpov/projects/self/mpm-service/service/stores/cron.log',
        },
        'prod': {
            'os_user': 'dockeruser',
            'intepreter_path': '/usr/local/bin/python3',
            'command_path': '/home/dockeruser/workdir/manage.py scheduler',
            'cron_log_path': '/home/dockeruser/workdir/cron.log',
        }
    }
    active_settings = settings[mode]

    job_min_frequency = 5
    job_max_frequency = 60
    valid_frequencies = {
        'min': 'раз в n минут',
        'max': 'раз в n часов',
    }

    @classmethod
    def _default_fr_type(cls):
        return 'min'

    @classmethod
    def min_frequency(cls):
        return cls.job_min_frequency

    @classmethod
    def max_frequency(cls):
        return cls.job_max_frequency

    @classmethod
    def frequency_choices(cls):
        return [(k, v) for k, v in cls.valid_frequencies.items()]

    def _is_prod(self):
        return self.mode == 'prod'

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
                continue

            if not wh.store.is_active():
                continue

            # err = OzonApi().update_stock(wh)
            err = OzonApi().fake_update_stock(wh)
            if err:
                _err(err)

            # todo - log to job execution log

    def _prop(self, prop):
        return self.active_settings[prop]

    def _add_jobs(self):
        _log('(scheduler) adding jobs to cron ...')

        user = self._prop('os_user')
        intepreter_path = self._prop('intepreter_path')
        command_path = self._prop('command_path')
        cron_log_path = self._prop('cron_log_path')

        app_users = ("admin",)  # todo - fetch schedule from db
        self._drop_jobs(user)
        cron = CronTab(user=user)

        for app_user in app_users:
            command_args = app_user
            job = cron.new(command=f'{intepreter_path} {command_path} {command_args} '
                                   f'>> {cron_log_path} 2>&1', comment=f'{self.update_stock_pattern}: {app_user}')
            job.minute.every(1)
            cron.write()
            _log(f'added a cron job for app user: {app_user}')

    def run(self):
        lock_filename = 'lock.file'
        if os.path.exists(lock_filename):
            return

        try:
            with open(lock_filename, 'w') as file:
                file.write(lock_filename)
                # explicitly start cron system service if this is production
                if self._is_prod():
                    os.system('service cron start')
                _log('ran scheduler successfully')
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

    @classmethod
    def is_valid_fr_type(cls, val):
        return val in cls.valid_frequencies.keys()

    @classmethod
    def validate_fr_val(cls, val):
        try:
            _int = int(val.strip())
            if _int < cls.min_frequency() or _int > cls.max_frequency():
                return f'Значение не входит в разрешенный диапазон значений ' \
                       f'({cls.min_frequency()}-{cls.max_frequency()})'
        except (ValueError, TypeError, Exception):
            return f'Значение не является валидным целым числом: {val}'

    @staticmethod
    def to_db_schedule(_type, val):
        return f'{_type} {val}'

    @classmethod
    def from_db_schedule(cls, src):
        parts = src.split(' ')

        if len(parts) > 1:
            fr_type, fr_val = parts[0], parts[1]
        else:
            fr_type, fr_val = parts[0], None

        if not cls.is_valid_fr_type(fr_type):
            fr_type = cls._default_fr_type()

        if cls.validate_fr_val(fr_val):
            fr_val = cls.min_frequency()

        return fr_type, fr_val

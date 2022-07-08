import os.path
import datetime

from crontab import CronTab

from .common import _log
from .common import _err
from .common import _exc
from .common import time_tracker
from .common import os_call

from .api import OzonApi
from ..models import StoreWarehouse
from ..models import UserJob


class Scheduler:
    mode = 'dev'
    # mode = 'prod'

    update_stock_pattern = 'update stock'
    # todo - get rid of hardcore and use dynamic condition
    settings = {
        'dev': {
            'os_user': 'dkarpov',
            'intepreter_path': '/home/dkarpov/projects/self/mpm-service/venv/bin/python',
            'command_path': '/home/dkarpov/projects/self/mpm-service/service/manage.py scheduler',
            'cron_log_path': '/home/dkarpov/projects/self/mpm-service/service/cron.log',
        },
        'prod': {
            'os_user': 'appuser',
            'intepreter_path': '/usr/local/bin/python3',
            'command_path': '/home/appuser/workdir/manage.py scheduler',
            'cron_log_path': '/home/appuser/workdir/cron.log',
        }
    }

    active_settings = settings[mode]
    job_min_frequency = 1
    job_max_frequency = 60
    valid_frequencies = {
        'min': 'Раз в n минут',
        'hr': 'Раз в n часов',
    }

    def run(self):
        lock_filename = 'scheduler_lock.file'
        if os.path.exists(lock_filename):
            return

        try:
            with open(lock_filename, 'w') as file:
                file.write(lock_filename)
        except (OSError, Exception) as err:
            err_msg = f'failed to run scheduler: {_exc(err)}'
            _err(err_msg)
            return

        # explicitly start cron system service if this is production
        if self._is_prod():
            os.system('service cron start')
        self._add_jobs()
        _log('ran scheduler successfully')

    @classmethod
    def _default_fr_type(cls):
        return 'min'

    @staticmethod
    def _is_min(val):
        return str(val).lower().strip() == 'min'

    @staticmethod
    def _is_hr(val):
        return str(val).lower().strip() == 'hr'

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

            err = OzonApi().update_stock(wh)
            # err = OzonApi().fake_update_stock(wh)
            if err:
                _err(err)

            # todo - log to job execution log

    def drop_user_jobs(self, username):
        cron = self._cron()
        count = 0

        for job in cron:
            if username in job.comment:
                job.remove()
                cron.write()
                count += 1

        if count:
            _log(f'total cron jobs deleted for app user "{username}": {count}')

    def get_user_jobs(self, username):
        result = {
            'jobs': self._get_user_jobs(username),
        }
        is_cron_running, err = self._is_cron_running()
        result['is_cron_running'] = is_cron_running
        if err:
            result['cron_check_error'] = err

        return result

    def _get_user_jobs(self, username):
        cron = self._cron()
        user_jobs = []
        for job in cron:
            if username in job.comment:
                schedule = job.schedule(date_from=datetime.datetime.now())
                _job = {
                    'active': job.is_enabled(),
                    'command': job.command,
                    'comment': job.comment,
                    'schedule': str(job.slices),  # any better options?
                    'next': schedule.get_next(),
                }
                user_jobs.append(_job)

        return user_jobs

    def _cron(self):
        user = self._prop('os_user')
        return CronTab(user=user)

    def _prop(self, prop):
        return self.active_settings[prop]

    def update_job(self, username, db_schedule):
        cron = self._cron()
        self._update_job(cron, username, db_schedule)

    def drop_job(self, username):
        cron = self._cron()
        for job in cron:
            # if job.comment == self._get_update_stock_job_repr(username):
            if username in job.comment:
                cron.remove(job)
                cron.write()
                _log(f'deleted a cron job for app user: {username}')

    @classmethod
    def _get_update_stock_job_repr(cls, username):
        return f'{cls.update_stock_pattern}: {username}'

    def _update_job(self, cron, username, db_schedule):
        """
        add a new job or update an existing one
        """
        action = 'updated'
        job = None
        job_repr = self._get_update_stock_job_repr(username)

        for cron_job in cron:
            if cron_job.comment == job_repr:
                job = cron_job
                break

        if job is None:
            action = 'added'
            intepreter_path = self._prop('intepreter_path')
            command_path = self._prop('command_path')
            cron_log_path = self._prop('cron_log_path')
            command_args = username
            job = cron.new(command=f'{intepreter_path} {command_path} {command_args} '
                                   f'>> {cron_log_path} 2>&1', comment=job_repr)

        fr_type, fr_val = self.from_db_schedule(db_schedule)
        if self._is_min(fr_type):
            job.minute.every(fr_val)
        elif self._is_hr(fr_type):
            job.hour.every(fr_val)

        cron.write()
        _log(f'{action} a cron job for app user: {username}')

    # noinspection PyUnresolvedReferences
    def _add_jobs(self):
        _log('(scheduler) start adding jobs to cron ...')
        self._drop_jobs()  # drop existing jobs

        app_valid_jobs = ('ozon_stock_update',)
        user_jobs = UserJob.objects.filter(active=True).filter(job__code__in=app_valid_jobs)
        if not len(user_jobs):
            _log('no active user jobs fetched from db (ozon stock update jobs only)')
            return

        cron = self._cron()
        for user_job in user_jobs:

            username = user_job.user.username
            db_schedule = user_job.schedule

            if not self.is_valid_schedule(user_job.schedule):
                _log(f'skipping invalid db job for user "{username}": {db_schedule}')
                continue

            self._update_job(cron, username, db_schedule)

        _log('(scheduler) done adding jobs to cron ...')

    def _drop_jobs(self):
        cron = self._cron()
        for job in cron:
            if self.update_stock_pattern in job.comment:
                _log(f'removing cron job: {job.comment}')
                cron.remove(job)
                cron.write()

    @classmethod
    def is_valid_schedule(cls, val):
        parts = val.split(' ')
        return len(parts) > 1 and cls.is_valid_fr_type(parts[0]) and not cls.validate_fr_val(parts[1])

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

    @classmethod
    def schedule_human_repr(cls, val):
        if not cls.is_valid_schedule(val):
            return f'Неверный формат расписания: {val}'
        fr_type, fr_val = cls.from_db_schedule(val)
        return f'{cls.valid_frequencies.get(fr_type, "")}: {fr_val}'

    @staticmethod
    def to_db_schedule(_type, val):
        return f'{_type} {val}'

    @classmethod
    def from_db_schedule(cls, val):
        parts = val.split(' ')

        if len(parts) > 1:
            fr_type, fr_val = parts[0], parts[1]
        else:
            fr_type, fr_val = parts[0], None

        if not cls.is_valid_fr_type(fr_type):
            fr_type = cls._default_fr_type()

        if cls.validate_fr_val(fr_val):
            fr_val = cls.min_frequency()

        return fr_type, fr_val

    @staticmethod
    def _is_cron_running():
        cmd = 'service cron status'
        status, err = os_call(cmd)
        if err:
            return None, err
        return status == 0, None

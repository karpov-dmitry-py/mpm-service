import logging
import django

import sys
sys.path.append("..")

from .helpers.scheduler import Scheduler
# noinspection PyProtectedMember
from .helpers.common import _log
# noinspection PyProtectedMember
from .helpers.common import _exc

try:
    from uwsgidecorators import spool
except (ImportError, Exception):
    def spool(func):
        def func_wrapper(**arguments):
            return func(arguments)

        return func_wrapper

django.setup()
logger = logging.getLogger(__name__)

try:
    import uwsgi


    def my_spooler(env):
        return uwsgi.SPOOL_OK


    uwsgi.spooler = my_spooler
except (ImportError, Exception) as err:
    _log(f'failed to import uwsgi: {_exc(err)}')


@spool
def update_ozon_stocks(arguments):
    username = arguments.get('username', '')
    Scheduler().update_ozon_stocks(username)

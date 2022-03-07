# noinspection PyProtectedMember
import os
import django

from stores.helpers.common import _log
# noinspection PyProtectedMember
from stores.helpers.common import _exc

try:
    from uwsgidecorators import spool
except (ImportError, Exception):
    def spool(func):
        def func_wrapper(**arguments):
            return func(arguments)

        return func_wrapper

try:
    import uwsgi
except (ImportError, Exception) as err:
    # _log(f'failed to import uwsgi: {_exc(err)}')
    pass

os.environ['DJANGO_SETTINGS_MODULE'] = 'service.settings'
django.setup()


# noinspection PyBroadException
@spool
def update_ozon_stocks(arguments):
    fnc = 'update_ozon_stocks'
    username = arguments.get('username', '')
    _log(f'calling "{fnc}" with username "{username}" ...')
    try:
        from stores.helpers.scheduler import Scheduler
        Scheduler().update_ozon_stocks(username)
        return uwsgi.SPOOL_OK
    except (ImportError, Exception) as err:
        _log(f'failed to call "{fnc}" with username "{username}": {_exc(err)}')
        return uwsgi.SPOOL_RETRY

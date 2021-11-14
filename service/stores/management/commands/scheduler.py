from django.core.management.base import BaseCommand

# import os
# import sys
# from pathlib import Path

# sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
# file = Path(__file__).resolve()
# package_root_directory = file.parents[1]
# sys.path.append(str(package_root_directory))
# for path in sys.path:
#     print(f'(scheduler) sys path: {path}')

from ...helpers.scheduler import Scheduler
from ...helpers.common import _log


class Command(BaseCommand):
    help = 'run a cron job ()'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='username to run job')

    def handle(self, *args, **kwargs):
        username = kwargs.get('username')
        msg = f'(command) start updating stocks for username: {username}'
        _log(msg)
        Scheduler().update_ozon_stocks(username)

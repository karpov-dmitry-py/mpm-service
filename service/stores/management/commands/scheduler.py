from django.core.management.base import BaseCommand

from ...helpers.scheduler import Scheduler
# noinspection PyProtectedMember
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

import time
import uwsgidecorators
from common import _log


@uwsgidecorators.timer(20, target="mule")
def periodic_task(signal: int):
    _log(f'periodic task called with signal {signal}')
    periodic_payload()


def periodic_payload():
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


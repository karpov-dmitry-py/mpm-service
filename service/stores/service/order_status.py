from ..models import OrderStatus
from ..models import OrderMarketplaceStatus
from ..models import Marketplace


# noinspection PyUnresolvedReferences
class OrderStatusService:
    _status_model = OrderStatus
    _mp_model = Marketplace
    _mp_status_model = OrderMarketplaceStatus

    def __init__(self):
        self._fetch_statuses()

    def _fetch_statuses(self):
        self._items = {item.code: item for item in self._status_model.objects.all()}
        self._mp_items = dict()
        for mp in self._mp_model.objects.all():
            self._mp_items[mp] = {item.code: item for item in self._mp_status_model.objects.all()}

    def get_by_code(self, code):
        return self._items.get(code, None)

    def get_by_mp_status(self, marketplace, status, substatus):
        code = self._get_mp_status_code(status, substatus)
        return self._mp_items.get(marketplace, {}).get(code)

    @classmethod
    def _get_mp_status_code(cls, status, substatus=None):
        _repr = f'{status.upper()}/{substatus.upper()}' if substatus else status.upper()
        return _repr

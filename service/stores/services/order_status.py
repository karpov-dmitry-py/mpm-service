from ..models import OrderStatus
from .mp_order_status import MarketplaceOrderStatus


# noinspection PyUnresolvedReferences
class OrderStatusService:
    _model = OrderStatus

    def __init__(self):
        self._fetch_statuses()

    def _fetch_statuses(self):
        self._items = {item.code: item for item in self._model.objects.all()}
        self._mp_status_service = MarketplaceOrderStatus()
        self._mp_items = self._mp_status_service.get_statuses()

    def get_by_code(self, code):
        return self._items.get(code, None)

    def get_by_mp_status(self, marketplace, status, substatus):
        code = self._get_mp_status_code(status, substatus)
        mp_status = self._mp_items.get(marketplace, {}).get(code)
        if mp_status:
            return mp_status.status

    @classmethod
    def _get_mp_status_code(cls, status, substatus=None):
        _repr = f'{status.upper()}/{substatus.upper()}' if substatus else status.upper()
        return _repr

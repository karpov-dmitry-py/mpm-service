from ..models import OrderMarketplaceStatus
from ..models import Marketplace


# noinspection PyUnresolvedReferences
class MarketplaceOrderStatus:
    _mp_model = Marketplace
    _status_model = OrderMarketplaceStatus

    def __init__(self):
        self._fetch_statuses()

    def _fetch_statuses(self):
        self._items = {}
        for mp in self._mp_model.objects.all():
            self._items[mp] = {item.code: item for item in self._status_model.objects.filter(marketplace=mp)}

    def get_statuses(self):
        return self._items

from ..models import OrderStatus


# noinspection PyUnresolvedReferences
class OrderStatusService:
    _model = OrderStatus

    def __init__(self):
        self._items = self._fetch_statuses()

    def _fetch_statuses(self):
        return {item.code: item for item in self._model.objects.all()}

    def get_status(self, code):
        return self._items.get(code, None)

import datetime

from ..models import Order
from ..models import OrderItem
from ..models import OrderShipment


class OrderService:

    def create(self, data, items, shipments):
        # order
        items_total = self._get_items_total(items)
        subsidy_total = self._get_subsidy_total(items)
        total = items_total + subsidy_total

        order = Order(
            marketplace=data.get('marketplace'),
            order_marketplace_id=data.get('order_marketplace_id'),
            store=data.get('store'),
            store_warehouse=data.get('store_warehouse'),
            region=data.get('region'),
            items_total=items_total,
            subsidy_total=subsidy_total,
            total=total,
            user=data.get('user'),
            created_at=datetime.datetime.now()
        )

        try:
            order.save()
        except (OSError, Exception) as e:
            return None, f'failed to save order: {str(e)}'

        # items
        err = self._save_items(order, items)
        if err:
            return None, err

        # shipments
        err = self._save_shipments(order, shipments)
        if err:
            return None, err

        return order.pk, None

    @staticmethod
    def _save_items(order, items):
        for sku, item in items.items():
            order_item = OrderItem(
                order=order,
                good=item.get('good'),
                count=item.get('count'),
                price=item.get('price'),
            )

            try:
                order_item.save()
            except (OSError, Exception) as e:
                return None, f'failed to save order item with sku "{sku}": {str(e)}'

    @staticmethod
    def _save_shipments(order, shipments):
        for i, item in enumerate(shipments, start=1):
            shp_item = OrderShipment(
                order=order,
                shipment_id=item.get('id'),
                shipment_date=item.get('date'),
            )

            try:
                shp_item.save()
            except (OSError, Exception) as e:
                return None, f'failed to save order shipment # {i}: {str(e)}'

    @staticmethod
    def _get_items_total(items):
        # todo - use one liner
        total = 0
        for item in items.values():
            total += item.get('count', 0) * item.get('price', 0)
        return total

    @staticmethod
    def _get_subsidy_total(items):
        return 0

    def update(self, order_id):
        pass

    def update_status(self, order_id, status_id):
        pass

    def get_total(self, order_id):
        pass

    def delete(self, order_id):
        pass

import datetime
import pytz

from ..models import Order
from ..models import OrderItem
from ..models import OrderShipment

from ..helpers.managers import user_qs
from ..helpers.common import now_with_project_tz

from .order_status import OrderStatusService


class OrderService:

    def __init__(self):
        self._status_service = OrderStatusService()

    def create(self, data, items, shipments):
        # order
        items_total = self._get_items_total(items)
        subsidy_total = data.get('subsidy_total', 0)
        total = items_total + subsidy_total
        status = self._status_service.get_status('created')

        order = Order(
            marketplace=data.get('marketplace'),
            order_marketplace_id=data.get('order_marketplace_id'),
            store=data.get('store'),
            store_warehouse=data.get('store_warehouse'),
            region=data.get('region'),
            status=status,
            items_total=items_total,
            subsidy_total=subsidy_total,
            total=total,
            user=data.get('user'),
            created_at=now_with_project_tz(),
        )

        existing_order, err = self._get_order(order)

        if err:
            return None, err
        if existing_order:
            order = self._update_order(existing_order=existing_order, new_order=order)

        order, err = self._save_order(order)
        if err:
            return None, err

        # items
        err = self._save_items(order, items)
        if err:
            return None, err

        # shipments
        err = self._save_shipments(order, shipments)
        if err:
            return None, err

        return order, None

    def update(self, order_id):
        pass

    def update_status(self, order_id, status_id):
        pass

    def get_by_marketplace_id(self, order_marketplace_id, marketplace, user):
        order = Order(
            order_marketplace_id=order_marketplace_id,
            marketplace=marketplace,
            user=user,
        )

        existing_order, err = self._get_order(order)
        if err:
            return None, err

        return existing_order, None

    def get_total(self, order_id):
        pass

    def delete(self, order_id):
        pass

    @staticmethod
    def _save_order(order):
        try:
            order.save()
            return order, None
        except (OSError, Exception) as e:
            return None, f'failed to save order {order.order_marketplace_id}: {str(e)}'

    @staticmethod
    def _get_order(order):
        try:
            orders = user_qs(Order, order.user). \
                filter(marketplace=order.marketplace). \
                filter(order_marketplace_id=order.order_marketplace_id). \
                order_by('-created_at')
            if orders:
                return orders[0], None
            return None, None
        except (OSError, Exception) as e:
            return None, f'failed to fetch order "{order.order_marketplace_id}" from db: {str(e)}'

    @staticmethod
    def _update_order(existing_order, new_order):
        attrs = ('store', 'store_warehouse', 'status', 'region', 'items_total', 'subsidy_total', 'total', 'comment')
        for attr in attrs:
            if getattr(existing_order, attr) != getattr(new_order, attr):
                setattr(existing_order, attr, getattr(new_order, attr))

        return existing_order

    @staticmethod
    def _save_items(order, items):
        if order.id:
            try:
                order.items.all().delete()
            except (OSError, Exception) as e:
                return None, f'failed to delete old items for order "{order.order_marketplace_id}": {str(e)}'

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
                return None, f'failed to save order item with sku "{sku}" ' \
                             f'for order "{order.order_marketplace_id}": {str(e)}'

    @staticmethod
    def _save_shipments(order, shipments):
        if order.id:
            try:
                order.shipments.all().delete()
            except (OSError, Exception) as e:
                return None, f'failed to delete old shipments for order "{order.order_marketplace_id}": {str(e)}'

        for i, item in enumerate(shipments, start=1):
            shp_item = OrderShipment(
                order=order,
                shipment_id=item.get('id'),
                shipment_date=item.get('date'),
            )

            try:
                shp_item.save()
            except (OSError, Exception) as e:
                return None, f'failed to save order shipment # {i} for order "{order.order_marketplace_id}": {str(e)}'

    @staticmethod
    def _get_items_total(items):
        # todo - use one liner
        total = 0
        for item in items.values():
            total += item.get('count', 0) * item.get('price', 0)
        return total

    @staticmethod
    def _get_subsidy_total():
        return 0

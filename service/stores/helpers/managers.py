# from .common import _exc
# from .common import _err
from .common import _log

import json
import time

from ..models import GoodsCategory
from ..models import GoodsBrand
from ..models import Warehouse
from ..models import Good
from ..models import Stock


class StockManager:

    @staticmethod
    def get_user_stock(user):
        # noinspection PyUnresolvedReferences
        rows = Stock.objects.filter(user=user).order_by('good')
        goods = rows.values_list('good').distinct()
        items = []
        for good_id in goods:
            good_rows = rows.filter(good_id=good_id)
            stocks = dict()
            total_amount = 0

            # good's stock rows
            for row in good_rows:
                total_amount += row.amount
                wh_stock = stocks.get(row.warehouse)
                if not wh_stock:
                    stocks[row.warehouse] = {
                        'amount': row.amount,
                        'date_updated': row.date_updated,
                    }
                    continue
                stocks[row.warehouse]['amount'] += row.amount
                if row.date_updated > stocks[row.warehouse]['date_updated']:
                    stocks[row.warehouse]['date_updated'] = row.date_updated

            # noinspection PyUnboundLocalVariable
            good_result = {
                'good': row.good,
                'total_amount': total_amount,
                'stocks': stocks
            }
            items.append(good_result)
        return items

    @staticmethod
    def _condition_attrs(condition):
        _type = _get_text_by_val(get_stock_condition_types, condition.get('type'))
        _field = _get_text_by_val(get_stock_condition_fields, condition.get('field'))
        return f'{_type} - {_field}'

    # noinspection PyTypeChecker
    @staticmethod
    def validate_stock_setting_content(content, user):
        start = time.time()
        content = content.strip()
        if not content:
            err = 'в настройке нет условий'
            return err

        try:
            conditions = json.loads(content)
        except (json.JSONDecodeError, Exception):
            err = f'Не валидное или пустое содержание настройки. Добавьте условия.'
            return err

        null = 'null'

        # type
        errors = []
        for i, cnd in enumerate(conditions, start=1):
            _type = cnd['type']
            if _type is None:
                err = f'не указан тип в условии № {i}'
                errors.append(err)
        if errors:
            err = ', '.join(errors)
            return err

        # field
        errors = []
        for i, cnd in enumerate(conditions, start=1):
            field = cnd['field']
            if field == null:
                err = f'не указано поле условия № {i}'
                errors.append(err)
        if errors:
            err = ', '.join(errors)
            return err

        # duplicates by type and field
        # noinspection PyUnresolvedReferences
        errors = dict()
        for item in conditions:
            item_attrs = StockManager._condition_attrs(item)
            matched = 0
            for cnd in conditions:
                if StockManager._condition_attrs(cnd) == item_attrs:
                    matched += 1
                    if matched > 1:
                        err = f'есть дубли по типу и полю условия: {item_attrs}'
                        if errors.get(err) is None:
                            errors[err] = 0
                        errors[err] += 1
                        break
        if errors:
            err = ', '.join(errors.keys())
            return err

        # incl type, min stock
        errors = []
        inc_types = ('include', 'exclude',)
        for i, cnd in enumerate(conditions, start=1):
            _type = cnd['type']
            if _type in inc_types:
                if cnd['include_type'] == null:
                    err = f'не указан вид включения-исключения в условии № {i}'
                    errors.append(err)
            elif _type == 'stock':
                min_stock = cnd['min_stock']
                if not _is_uint(min_stock):
                    err = f'не указан корректный минимальный остаток в условии № {i}'
                    errors.append(err)
        if errors:
            err = ', '.join(errors)
            return err

        attr = 'id'
        # wh
        # noinspection PyTypeChecker
        whs = _get_user_qs(Warehouse, user)
        wh_ids = _get_attr_list_from_items(whs, attr)
        wh_dict = _get_dict_by_attr_from_items(whs, attr)

        # noinspection PyTypeChecker
        brands = _get_user_qs(GoodsBrand, user)
        brand_ids = _get_attr_list_from_items(brands, attr)
        brand_dict = _get_dict_by_attr_from_items(brands, attr)

        cats = _get_user_qs(GoodsCategory, user)
        cat_ids = _get_attr_list_from_items(cats, attr)
        cat_dict = _get_dict_by_attr_from_items(cats, attr)

        attr = 'sku'
        goods = _get_user_qs(Good, user)
        good_ids = _get_attr_list_from_items(goods, attr)
        good_dict = _get_dict_by_attr_from_items(goods, attr)

        db_data = {
            'warehouse': {
                'ids': wh_ids,
                'dict': wh_dict,
            },
            'brand': {
                'ids': brand_ids,
                'dict': brand_dict,
            },
            'cat': {
                'ids': cat_ids,
                'dict': cat_dict
            },
            'good': {
                'ids': good_ids,
                'dict': good_dict,
            },
        }

        # values
        errors = []
        for i, cnd in enumerate(conditions, start=1):
            field = cnd['field']
            values = cnd['values']

            if not values:
                err = f'не указан список значений по полю условия № {i}'
                errors.append(err)
                continue

            for field_name in db_data:
                if field != field_name:
                    continue

                _ids = db_data[field_name]['ids']
                # if not all(val in field_ids for val in values):
                for val in values:
                    if val not in _ids:
                        err = f'указаны товар не текущего пользователя в условии № {i}: {val}'
                        errors.append(err)

        if errors:
            err = ', '.join(errors)
            return err

        # intersection by values (incl - excl)
        errors = []
        # todo
        # for i, cnd in enumerate(conditions, start=1):
        #     _type = cnd['type']

        # time track
        # end = time.time()
        # total_time = end - start
        # _log(f'check total time: {total_time}')

    @staticmethod
    def calculate_stock_setting(setting):
        pass


def _is_uint(src):
    try:
        _int = int(src)
        return _int > 0
    except (TypeError, BaseException):
        return False


def _get_text_by_val(func, val):
    for item in func():
        if item['val'] and item['val'] == val:
            return item['text']


def get_stock_condition_types():
    items = [
        {
            'val': None,
            'text': 'Выберите тип условия',
        },
        {
            'val': 'include',
            'text': 'Включить',
        },
        {
            'val': 'exclude',
            'text': 'Исключить',
        },
        {
            'val': 'stock',
            'text': 'Остаток',
        },
    ]
    return items


def get_stock_condition_fields():
    items = [
        {
            'val': None,
            'text': 'Выберите поле условия',
        },
        {
            'val': 'warehouse',
            'text': 'Склад',
        },
        {
            'val': 'cat',
            'text': 'Категория',
        },
        {
            'val': 'brand',
            'text': 'Бренд',
        },
        {
            'val': 'good',
            'text': 'Товар',
        },
    ]
    return items


def get_stock_include_types():
    items = [
        {
            'val': 'in_list',
            'text': 'В списке',
        },
        {
            'val': 'not_in_list',
            'text': 'Не в списке',
        },
    ]
    return items


def _get_user_qs(model, user):
    qs = model.objects.filter(user=user)
    return qs


def _get_attr_list_from_items(items, attr_name):
    _items = [str(getattr(item, attr_name)) for item in items]
    return _items


def _get_dict_by_attr_from_items(items, attr_name):
    name = 'name'
    _dict = {str(getattr(item, attr_name)): getattr(item, name) for item in items}
    return _dict

# from .common import _exc
# from .common import _err
# from .common import _log

import json
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
        _type = _get_text_by_val(get_stock_condition_types, condition.get("type"))
        _field = _get_text_by_val(get_stock_condition_fields, condition.get("field"))
        return f'{_type} - {_field}'

    @staticmethod
    def validate_stock_setting_content(content):
        content = content.strip()
        if not content:
            err = 'в настройке нет условий'
            return err

        try:
            conditions = json.loads(content)
        except (json.JSONDecodeError, Exception):
            err = f'Не валидный json в условиях. Добавьте новые условия.'
            return err

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
            if type in inc_types:
                if cnd['include_type'] is None:
                    err = f'не указан вид включения-исключения в условии № {i}'
                    errors.append(err)
            elif type == 'stock':
                min_stock = cnd['min_stock']
                if not _is_uint(min_stock):
                    err = f'не указан корректный минимальный остаток в условии № {i}'
                    errors.append(err)
        if errors:
            err = ', '.join(errors)
            return err

        # field

        # values

        # intersection (incl - excl)

        return None

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

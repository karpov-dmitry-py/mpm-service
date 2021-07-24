import json
from collections import defaultdict

from threading import Thread
from threading import Lock

# from multiprocessing import Process
# from multiprocessing import RLock as PLock

from django.db.models import Sum
from django.db.models import Max

from .common import _log
from .common import _exc
from .common import _err
from .common import time_tracker

from ..models import GoodsCategory
from ..models import GoodsBrand
from ..models import Warehouse
from ..models import Good
from ..models import Stock


class StockManager:
    max_threads = 100

    def __init__(self):
        self._lock = Lock()
        # self._lock = PLock()

    @staticmethod
    def _wh_repr(wh):
        return wh.id, wh.name, wh.kind.name

    def _get_stock_by_good(self, rows, good_id, whs_dict, result_items):
        # with self._lock:
        good_rows = []
        for row in rows:
            if row.good_id == good_id:
                good_rows.append(row)
        good = good_rows[0].good

        stocks = defaultdict(dict)
        for row in good_rows:
            if not stocks[row.warehouse]:
                stocks[row.warehouse] = {
                    'total_amount': 0,
                    'date_updated': None,
                }
                stocks[row.warehouse]['total_amount'] += row.amount
                if stocks[row.warehouse]['date_updated'] is None \
                        or stocks[row.warehouse]['date_updated'] < row.date_updated:
                    stocks[row.warehouse]['date_updated'] = row.date_updated

        # stocks = good_rows.values('warehouse') \
        #     .annotate(total_amount=Sum('amount')) \
        #     .annotate(max_date_updated=Max('date_updated')).filter(total_amount__gt=0)

        _stocks = []
        total_amount = 0
        for wh, stock_data in stocks.items():
            amount = stock_data['total_amount']
            total_amount += amount

            _dict = {
                'wh_type': wh.kind.name,
                'wh_name': wh.name,
                'wh_id': str(wh.id),
                'warehouse': wh.id,
                'total_amount': amount,
                'date_updated': stock_data['date_updated'],
            }
            _stocks.append(_dict)

        # total_amount = _sum_list_of_dicts_by_key(_stocks, 'total_amount')
        if total_amount == 0:
            return
        #
        # stocks = list(stocks)
        # for stock_dict in stocks:
        #     wh = whs_dict[stock_dict['warehouse']]
        #     # with self._lock:
        #     stock_dict['wh_type'] = wh.kind.name
        #     stock_dict['wh_name'] = wh.name
        #     stock_dict['wh_id'] = str(wh.id)

        # noinspection PyUnboundLocalVariable
        good_result = {
            # 'good': good_rows[0].good,
            'good': good,
            'total_amount': total_amount,
            'stocks': _stocks,
        }
        # with self._lock:
        result_items.append(good_result)

    def _get_stock_by_good_db(self, rows, good_id, whs_dict, result_items):
        # with self._lock:
        good_rows = rows.filter(good_id=good_id)
        stocks = good_rows.values('warehouse') \
            .annotate(total_amount=Sum('amount')) \
            .annotate(max_date_updated=Max('date_updated')).filter(total_amount__gt=0)

        total_amount = _sum_list_of_dicts_by_key(stocks, 'total_amount')
        if total_amount == 0:
            return

        stocks = list(stocks)
        for stock_dict in stocks:
            wh = whs_dict[stock_dict['warehouse']]
            # with self._lock:
            stock_dict['wh_type'] = wh.kind.name
            stock_dict['wh_name'] = wh.name
            stock_dict['wh_id'] = str(wh.id)

        # noinspection PyUnboundLocalVariable
        good_result = {
            'good': good_rows[0].good,
            'total_amount': total_amount,
            'stocks': stocks,
        }
        # with self._lock:
        result_items.append(good_result)

    def _collect_stocks_by_good_id(self, _id, rows, _dict):
        for row in rows:
            if row.good.id == id:
                with self._lock:
                    _dict[_id].append(row)

    @time_tracker('get_user_stock_threading_memory')
    def get_user_stock(self, user):
        # noinspection PyUnresolvedReferences,PyTypeChecker
        whs = _get_user_qs(Warehouse, user)
        whs_dict = _get_dict_by_attr_from_items(whs, 'id')

        # noinspection PyTypeChecker
        rows = _get_user_qs(Stock, user).filter(amount__gt=0).order_by('good')
        goods = rows.values_list('good').distinct()
        good_ids = [good_id[0] for good_id in goods]

        # threads = []
        # _stocks = defaultdict(list)
        # start = time.time()
        # for i, _id in enumerate(good_ids, start=1):
        #     _log(f'Processing _id # {i}')
        #     thread = Thread(target=self._collect_stocks_by_good_id, args=(_id, rows, _stocks))
        #     thread.start()
        #     threads.append(thread)
        #
        # for thread in threads:
        #     thread.join()
        #
        # end = time.time()
        # _log(f'stocks by good id took: {end-start}')

        items = []
        iteration = 0

        while len(good_ids):

            iteration += 1
            _log(f'iteration # {iteration} ...')

            if not len(good_ids):
                break

            chunk = good_ids[:self.max_threads]
            if not len(chunk):
                break

            good_ids = good_ids[self.max_threads:]
            threads = []

            for good_id in chunk:
                thread = Thread(target=self._get_stock_by_good, args=(rows, good_id, whs_dict, items,))
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()

        return items

    @time_tracker('get_user_stock_threading')
    def get_user_stock_threading_read_db(self, user):
        # noinspection PyUnresolvedReferences,PyTypeChecker
        whs = _get_user_qs(Warehouse, user)
        whs_dict = _get_dict_by_attr_from_items(whs, 'id')

        # noinspection PyTypeChecker
        rows = _get_user_qs(Stock, user).filter(amount__gt=0).order_by('good')
        goods = rows.values_list('good').distinct()
        items = []

        good_ids = [good_id[0] for good_id in goods]
        iteration = 0

        while len(good_ids):
            iteration += 1
            _log(f'iteration # {iteration} ...')

            if not len(good_ids):
                break

            chunk = good_ids[:self.max_threads]
            if not len(chunk):
                break

            good_ids = good_ids[self.max_threads:]
            threads = []

            for good_id in chunk:
                thread = Thread(target=self._get_stock_by_good, args=(rows, good_id, whs_dict, items,))
                # thread = Process(target=self._get_stock_by_good, args=(rows, good_id, whs_dict, items,))
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()

        return items

    @time_tracker('get_user_stock')
    def get_user_stock_sync(self, user):
        # noinspection PyUnresolvedReferences,PyTypeChecker
        whs = _get_user_qs(Warehouse, user)
        whs_dict = _get_dict_by_attr_from_items(whs, 'id')

        # noinspection PyTypeChecker
        rows = _get_user_qs(Stock, user).order_by('good')
        goods = rows.values_list('good').distinct()
        items = []
        for good_id in goods:
            good_rows = rows.filter(good=good_id[0])
            stocks = good_rows.values('warehouse') \
                .annotate(total_amount=Sum('amount')) \
                .annotate(max_date_updated=Max('date_updated')).filter(total_amount__gt=0)

            total_amount = _sum_list_of_dicts_by_key(stocks, 'total_amount')
            if total_amount == 0:
                continue

            stocks = list(stocks)
            for stock_dict in stocks:
                wh = whs_dict[stock_dict['warehouse']]
                stock_dict['wh_type'] = wh.kind.name
                stock_dict['wh_name'] = wh.name
                stock_dict['wh_id'] = str(wh.id)

            # noinspection PyUnboundLocalVariable
            good_result = {
                'good': good_rows[0].good,
                'total_amount': total_amount,
                'stocks': stocks,
            }
            items.append(good_result)

        return items

    @staticmethod
    @time_tracker('get_user_stock_dict')  # old
    def get_user_stock_dict(user):
        # noinspection PyUnresolvedReferences,PyTypeChecker
        whs = _get_user_qs(Warehouse, user)
        whs_dict = _get_dict_by_attr_from_items(whs, 'id')

        # noinspection PyTypeChecker
        rows = _get_user_qs(Stock, user).order_by('good')
        goods = rows.values_list('good').distinct()
        items = []
        for good_id in goods:
            good_rows = rows.filter(good=good_id[0])
            stocks = good_rows.values('warehouse') \
                .annotate(total_amount=Sum('amount')) \
                .annotate(max_date_updated=Max('date_updated'))

            _stocks = dict()
            for stock_dict in stocks:
                wh = whs_dict[stock_dict['warehouse']]
                _stocks[wh] = stock_dict

            # noinspection PyUnboundLocalVariable
            good_result = {
                'good': good_rows[0].good,
                'total_amount': _sum_list_of_dicts_by_key(stocks, 'total_amount'),
                'stocks': stocks,
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
        content = content.strip()
        if not content:
            err = 'в настройке нет условий'
            return err

        try:
            conditions = json.loads(content)
        except (json.JSONDecodeError, Exception):
            err = f'Не валидное или пустое содержание настройки. Добавьте условия.'
            return err

        if not conditions:
            err = 'в настройке нет условий'
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
        # wh_dict = _get_dict_by_attr_from_items(whs, attr)

        # noinspection PyTypeChecker
        brands = _get_user_qs(GoodsBrand, user)
        brand_ids = _get_attr_list_from_items(brands, attr)
        # brand_dict = _get_dict_by_attr_from_items(brands, attr)

        cats = _get_user_qs(GoodsCategory, user)
        cat_ids = _get_attr_list_from_items(cats, attr)
        # cat_dict = _get_dict_by_attr_from_items(cats, attr)
        #
        attr = 'sku'
        goods = _get_user_qs(Good, user)
        good_ids = _get_attr_list_from_items(goods, attr)
        # good_dict = _get_dict_by_attr_from_items(goods, attr)

        db_data = {
            'warehouse': {
                'ids': wh_ids,
                # 'dict': wh_dict,
            },
            'brand': {
                'ids': brand_ids,
                # 'dict': brand_dict,
            },
            'cat': {
                'ids': cat_ids,
                # 'dict': cat_dict
            },
            'good': {
                'ids': good_ids,
                # 'dict': good_dict,
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
                for val in values:
                    if val not in _ids:
                        err = f'указаны товар не текущего пользователя в условии № {i}: {val}'
                        errors.append(err)

        if errors:
            err = ', '.join(errors)
            return err

        # check values intersection (incl - excl)
        # collect rows of types and values by field
        _dict = defaultdict(list)
        for i, cnd in enumerate(conditions, start=1):
            _field = cnd['field']
            _type = cnd['type']
            if _type in inc_types:
                _fld_dict = {
                    'type': _type,
                    'include_type': cnd['include_type'],
                    'values': cnd['values'],
                }
                _dict[_field].append(_fld_dict)

        # iterate over collected rows by field
        errors = []
        for field, rows in _dict.items():

            if len(rows) < 2:
                continue

            ids_set = set(db_data[field]['ids'])
            incl_set = None
            excl_set = None

            for row in rows:
                values_set = set(row['values'])

                # include
                if row['type'] == 'include':
                    if row['include_type'] == 'in_list':
                        _set = values_set.intersection(ids_set)
                    else:
                        _set = values_set.symmetric_difference(ids_set)
                    incl_set = _set

                # exclude
                else:
                    set_to_compare_with = ids_set if incl_set is None else incl_set
                    if row['include_type'] == 'in_list':
                        _set = values_set.intersection(set_to_compare_with)
                    else:
                        _set = values_set.symmetric_difference(set_to_compare_with)
                    excl_set = _set

            # total match -> error
            if incl_set == excl_set:
                _field = _get_text_by_val(get_stock_condition_fields, field)
                err = f'указаны взаимоисключающие списки значений (включить-исключить) по полю {_field}'
                errors.append(err)

        if errors:
            err = ', '.join(errors)
            return err

    @staticmethod
    @time_tracker('calculate_stock')
    def calculate_stock(settings, user):
        not_used = 'Не применяется'
        result = {
            'settings': dict(),
            'conditions': dict()
        }

        stocks = StockManager().get_user_stock(user)
        stocks = {item['good'].sku: item for item in stocks}  # from list to dict

        goods_count = len(stocks)
        for i, setting in enumerate(settings, start=1):
            _log(f'calculating setting # {i} ...')

            stocks, stocks_by_conditions = StockManager.calculate_stock_setting_content(setting.content, stocks)
            if i > 1 and len(stocks) == goods_count:
                result['settings'][setting.id] = not_used
            else:
                result['settings'][setting.id] = len(stocks)
                goods_count = len(stocks)

            result['conditions'][setting.id] = stocks_by_conditions

        return result

    @staticmethod
    def calculate_stock_setting_content(content, stocks):

        # test
        # return stocks

        if not len(stocks):
            return stocks, '-'

        try:
            conditions = json.loads(content)
        except (json.JSONDecodeError, Exception) as err:
            err_msg = f'{_exc(err)}'
            _err(err_msg)
            return stocks, 'в настройке некорректный json'

        if not len(conditions):
            return stocks, 'в настройке нет условий'

        incl_types = 'include', 'exclude',
        conditions_stats = dict()

        for i, condition in enumerate(conditions, start=1):
            _type = condition['type']

            if _type in incl_types:
                stocks = StockManager._calculate_include_exclude(stocks, condition)

            elif _type == 'stock':
                stocks = StockManager._calculate_min_stock(stocks, condition)

            _log(f' --- condition # {i} - stocks {len(stocks)}')
            conditions_stats[i] = len(stocks)

        return stocks, conditions_stats

    @staticmethod
    def _calculate_include_exclude(stocks, condition):
        _type = condition['type']
        field = condition['field']
        incl_type = condition['include_type']
        values = condition['values']

        if field == 'warehouse':
            skus_to_remove = set()
            for sku, _dict in stocks.items():

                _stocks = _dict['stocks']
                new_stocks = []
                amount = 0

                for row in _stocks:
                    # in list
                    if (_type == 'include' and incl_type == 'in_list') \
                            or (_type == 'exclude' and incl_type == 'not_in_list'):
                        if row['wh_id'] in values:
                            new_stocks.append(row)
                            amount += row['total_amount']
                    else:
                        if row['wh_id'] not in values:
                            new_stocks.append(row)
                            amount += row['total_amount']

                if not new_stocks:
                    _dict['total_amount'] = 0
                    skus_to_remove.add(sku)
                else:
                    _dict['total_amount'] = amount
                    _dict['stocks'] = new_stocks
                stocks[sku] = _dict

            for sku in skus_to_remove:
                stocks.pop(sku, None)

        elif field == 'good':
            wanted_items = set()
            stock_skus = list(stocks.keys())

            for sku in stock_skus:
                if (_type == 'include' and incl_type == 'in_list') \
                        or (_type == 'exclude' and incl_type == 'not_in_list'):
                    if sku in values:
                        wanted_items.add(sku)
                else:
                    if sku not in values:
                        wanted_items.add(sku)

            for sku in stock_skus:
                if sku not in wanted_items:
                    stocks.pop(sku, None)

        elif field == 'brand' or field == 'cat':
            attr_names = {
                'brand': 'brand_id',
                'cat': 'category_id',
            }
            attr_name = attr_names[field]
            wanted_items = set()

            for sku, _dict in stocks.items():
                _id = str(getattr(_dict['good'], attr_name))
                if (_type == 'include' and incl_type == 'in_list') \
                        or (_type == 'exclude' and incl_type == 'not_in_list'):
                    if _id in values:
                        wanted_items.add(sku)
                else:
                    if _id not in values:
                        wanted_items.add(sku)

            for sku in list(stocks.keys()):
                if sku not in wanted_items:
                    stocks.pop(sku, None)

        return stocks

    @staticmethod
    def _calculate_min_stock(stocks, condition):
        field = condition['field']
        min_stock = int(condition['min_stock'])
        values = condition['values']

        if field == 'good':
            wanted_skus = set()
            for sku, _dict in stocks.items():
                if sku in values and _dict['total_amount'] >= min_stock:
                    wanted_skus.add(sku)

            for sku in list(stocks.keys()):
                if sku not in wanted_skus:
                    stocks.pop(sku, None)

        elif field == 'warehouse':
            skus_to_remove = set()
            for sku, _dict in stocks.items():

                _stocks = _dict['stocks']
                new_stocks = []
                amount = 0

                for row in _stocks:
                    if row['wh_id'] in values and row['total_amount'] >= min_stock:
                        new_stocks.append(row)
                        amount += row['total_amount']

                if not new_stocks:
                    # _dict['total_amount'] = 0
                    skus_to_remove.add(sku)
                else:
                    _dict['total_amount'] = amount
                    _dict['stocks'] = new_stocks

                stocks[sku] = _dict

            for sku in skus_to_remove:
                stocks.pop(sku, None)

        return stocks


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


@time_tracker('get_user_qs')
def _get_user_qs(model, user):
    qs = model.objects.filter(user=user)
    return qs


def _get_attr_list_from_items(items, attr_name):
    _items = [str(getattr(item, attr_name)) for item in items]
    return _items


def _get_dict_by_attr_from_items(items, attr_name):
    _dict = {getattr(item, attr_name): item for item in items}
    return _dict


def _sum_list_of_dicts_by_key(_list, key):
    _sum = 0
    for _dict in _list:
        _sum += _dict[key]
    return _sum

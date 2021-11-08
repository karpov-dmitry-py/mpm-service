import json
import copy
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from threading import Thread
from threading import Lock

from django.db.models import Sum
from django.db.models import Max

from .common import _log
from .common import _exc
from .common import _err
from .common import uwsgi_lock

from ..models import GoodsCategory
from ..models import GoodsBrand
from ..models import Warehouse
from ..models import Good
from ..models import Stock
from ..models import StoreWarehouse


class StockManager:
    goods_slice_size = 200
    goods_slice_handlers = 50
    setting_not_used_text = 'не применяется'

    def __init__(self):
        self._lock = Lock()

    @staticmethod
    def get_setting_not_used_text():
        return StockManager.setting_not_used_text

    @staticmethod
    def _wh_repr(wh):
        return wh.id, wh.name, wh.kind.name

    def _get_stock_by_good(self, rows, good_id, result_items):
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

        if total_amount == 0:
            return
        # noinspection PyUnboundLocalVariable
        good_result = {
            'good': good,
            'total_amount': total_amount,
            'stocks': _stocks,
        }
        with self._lock:
            result_items.append(good_result)

    def _get_stock_by_good_db(self, qs, good_id, stocks):
        good_rows = qs.filter(good_id=good_id)
        good = good_rows[0].good
        _stocks = good_rows.values('warehouse') \
            .annotate(total_amount=Sum('amount')) \
            .annotate(max_date_updated=Max('date_updated'))
        _stocks = list(_stocks)
        total_amount = _sum_list_of_dicts_by_key(_stocks, 'total_amount')
        good_result = {
            'good': good,
            'total_amount': total_amount,
            'stocks': _stocks,
        }
        with self._lock:
            stocks.append(good_result)

    def _collect_stocks_by_good_id(self, _id, rows, _dict):
        for row in rows:
            if row.good.id == id:
                with self._lock:
                    _dict[_id].append(row)

    @staticmethod
    def get_stocks_loop_read_db(qs, _ids):
        ids_count = len(_ids)
        stocks = []
        for i, _id in enumerate(_ids, start=1):
            _log(f'aggregating good {i} of {ids_count}')
            rows = qs.filter(good_id=_id)
            _stocks = rows.values('warehouse') \
                .annotate(total_amount=Sum('amount')) \
                .annotate(max_date_updated=Max('date_updated'))

            _stocks = list(_stocks)
            good = rows[0].good
            stocks.append({
                'good': good,
                'stocks': _stocks,
                'total_amount': _sum_list_of_dicts_by_key(_stocks, 'total_amount')
            })
        return stocks

    def get_stocks_loop_read_db_skus(self, qs, _ids, stocks):
        for i, _id in enumerate(_ids, start=1):
            rows = qs.filter(good_id=_id)
            _stocks = rows.values('warehouse') \
                .annotate(total_amount=Sum('amount')) \
                .annotate(max_date_updated=Max('date_updated'))

            _stocks = list(_stocks)
            good = rows[0].good
            with self._lock:
                stocks.append({
                    'good': good,
                    'stocks': _stocks,
                    'total_amount': _sum_list_of_dicts_by_key(_stocks, 'total_amount')
                })

    # noinspection PyTypeChecker
    @staticmethod
    def get_user_stock_goods(user):
        rows = _get_user_qs(Stock, user).filter(amount__gt=0).order_by('good')
        good_ids = rows.values_list('good', flat=True).distinct()
        good_rows = _get_user_qs(Good, user).filter(pk__in=good_ids)
        return good_rows

    # noinspection PyTypeChecker
    def get_user_stock(self, user, skus=None):
        qs = _get_user_qs(Stock, user).filter(amount__gt=0)
        if skus:
            qs = qs.filter(good__sku__in=skus)
        qs = qs.order_by('good')
        items = self._get_user_stock_threading(qs)

        return items

    def get_user_stock_old_threading_read_db(self, rows, good_ids):
        items = []
        iteration = 0
        while len(good_ids):
            iteration += 1
            _log(f'get stock iteration # {iteration} ...')

            if not len(good_ids):
                break

            chunk = good_ids[:self.goods_slice_size]
            if not len(chunk):
                break

            good_ids = good_ids[self.goods_slice_size:]
            threads = []

            for good_id in chunk:
                thread = Thread(target=self._get_stock_by_good_db, args=(rows, good_id, items,))
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()

        return items

    def _get_stock_by_sku_slice(self, qs, _ids, stocks):
        with ThreadPoolExecutor(max_workers=min(self.goods_slice_size, self.goods_slice_handlers)) as executor:
            for i, good_id in enumerate(_ids, start=1):
                executor.submit(self._get_stock_by_good_db, qs=qs, good_id=good_id, stocks=stocks)

    def _get_user_stock_threading(self, qs):
        stocks = []
        slices = []
        good_ids = qs.values_list('good', flat=True).distinct()

        while len(good_ids):
            _slice = good_ids[:self.goods_slice_size]
            if not len(_slice):
                break
            slices.append(_slice)
            good_ids = good_ids[self.goods_slice_size:]

        with ThreadPoolExecutor(max_workers=50) as executor:
            for i, _ids in enumerate(slices, start=1):
                executor.submit(self._get_stock_by_sku_slice, qs=qs, _ids=_ids, stocks=stocks)

        return stocks

    @staticmethod
    def get_user_stock_sync(user):
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

    # noinspection PyUnusedLocal,PyTypeChecker
    def calculate_stock_for_skus(self, user, skus, store_wh_id=None, aggregate_by_store=True):
        result = dict()
        whs = _get_user_qs(StoreWarehouse, user).order_by('id')
        if store_wh_id:
            whs = whs.filter(id=store_wh_id)

        if not whs:
            return result
        whs_count = whs.count()

        stocks = self.get_user_stock(user, skus)
        if not stocks:
            return result

        result = defaultdict(list)
        with ThreadPoolExecutor(max_workers=whs_count) as executor:
            for i, wh in enumerate(whs, start=1):
                # _log(f'applying stock settings for store warehouse {i} of {whs_count} ...')
                _stocks = stocks if whs_count == 1 else copy.deepcopy(stocks)
                executor.submit(self.calculate_stock_by_store_warehouse,
                                wh=wh, stocks=_stocks, result=result)

        result = dict(result)

        # aggregate result by store
        if aggregate_by_store:
            for sku, stock in result.items():
                store_stock = defaultdict(list)
                for row in stock:
                    store_stock[row['wh'].store].append(row)
                store_stock = dict(store_stock)
                result[sku] = store_stock

        return result

    # noinspection PyTypeChecker
    def calculate_stock_by_store_warehouse(self, wh, stocks, result):
        settings = wh.stock_settings.all()

        # use full current stock if store warehouse has no stock settings
        if not settings:
            for _dict in stocks:
                with self._lock:
                    result[_dict['good'].sku].append({'wh': wh, 'amount': _dict['total_amount']})
            return

        stock = self.calculate_stock_settings(settings, stocks, get_detailed_stocks=True)
        stocks_by_goods = stock['details']
        if stocks_by_goods:
            with self._lock:
                for k, v in stocks_by_goods.items():
                    result[k].extend(v)

    # noinspection PyTypeChecker
    @staticmethod
    def calculate_stock_settings(settings, stocks, get_detailed_stocks=False):
        not_used_text = StockManager.get_setting_not_used_text()
        result = {
            'settings': dict(),
            'conditions': dict(),
            'details': dict(),
        }
        stocks = {item['good'].sku: item for item in stocks}  # from list to dict
        goods_count = len(stocks)

        for i, setting in enumerate(settings, start=1):
            # _log(f'calculating setting # {i} ...')

            stocks, stocks_by_conditions = StockManager.calculate_stock_setting_content(setting.content, stocks)
            if i > 1 and len(stocks) == goods_count:
                result['settings'][setting.id] = not_used_text
            else:
                result['settings'][setting.id] = len(stocks)
                goods_count = len(stocks)

            result['conditions'][setting.id] = stocks_by_conditions

        if get_detailed_stocks and len(stocks):
            wh = settings[0].warehouse
            stocks_by_good = defaultdict(list)
            for k, v in stocks.items():
                stocks_by_good[k].append({'wh': wh, 'amount': v['total_amount']})
            result['details'] = dict(stocks_by_good)

        return result

    @staticmethod
    def calculate_stock_setting_content(content, stocks):
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

            # _log(f' --- condition # {i} - stocks {len(stocks)}')
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
                    wh_id = str(row['warehouse'])
                    # in list
                    if (_type == 'include' and incl_type == 'in_list') \
                            or (_type == 'exclude' and incl_type == 'not_in_list'):
                        if wh_id in values:
                            new_stocks.append(row)
                            amount += row['total_amount']
                    else:
                        if wh_id not in values:
                            new_stocks.append(row)
                            amount += row['total_amount']

                if not new_stocks:
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
        values = condition['values']
        condition['min_stock'] = 1 if not condition['min_stock'] else condition['min_stock']
        min_stock = int(condition['min_stock'])

        if field == 'good':
            unwanted_skus = set()
            for sku, _dict in stocks.items():
                if sku not in values:
                    unwanted_skus.add(sku)
                    continue

                if _dict['total_amount'] < min_stock:
                    unwanted_skus.add(sku)

            for sku in unwanted_skus:
                stocks.pop(sku, None)

        elif field == 'warehouse':
            skus_to_remove = set()
            for sku, _dict in stocks.items():

                _stocks = _dict['stocks']
                new_stocks = []
                amount = 0

                for row in _stocks:
                    if str(row['warehouse']) in values and row['total_amount'] >= min_stock:
                        new_stocks.append(row)
                        amount += row['total_amount']

                if not new_stocks:
                    skus_to_remove.add(sku)
                else:
                    _dict['total_amount'] = amount
                    _dict['stocks'] = new_stocks
                    stocks[sku] = _dict

            for sku in skus_to_remove:
                stocks.pop(sku, None)

        elif field == 'brand' or field == 'cat':
            attr_names = {
                'brand': 'brand_id',
                'cat': 'category_id',
            }
            attr_name = attr_names[field]
            unwanted_skus = set()

            for sku, _dict in stocks.items():
                if str(getattr(_dict['good'], attr_name)) not in values:
                    unwanted_skus.add(sku)
                    continue

                if _dict['total_amount'] < min_stock:
                    unwanted_skus.add(sku)

            for sku in unwanted_skus:
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

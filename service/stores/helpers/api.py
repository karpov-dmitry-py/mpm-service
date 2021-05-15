import random
import json
from collections import defaultdict
from collections.abc import Iterable

from django.http import JsonResponse

from ..models import Warehouse
from ..models import GoodsCategory
from ..models import GoodsBrand
from ..models import System
from ..models import Stock
from .common import new_uuid
from .common import _exc
from .common import _err
from .common import _log


# class for managing for own api
class API:
    api_ver = '1'
    required_headers = {
        'user-auth': 'HTTP_USER_AUTH',
        'token-auth': 'HTTP_TOKEN_AUTH',
    }

    @staticmethod
    def get_api_ver():
        return f'{API.api_ver}'

    @staticmethod
    def get_api_full_path():
        return f'api/v{API.get_api_ver()}'

    def _get_system_request_user(self, request):
        user_email, token, err = self._get_system_request_headers(request)
        if err:
            return None, err
        # noinspection PyUnresolvedReferences
        system_rows = System.objects.filter(user__email=user_email).filter(token=token)
        if not len(system_rows):
            return None, self._system_request_err()['response']
        return system_rows[0].user, None

    @staticmethod
    def _system_request_err(reason=None):
        reason = reason or 'wrong credentials provided'
        data = {
            'error': True,
            'reason': reason,
        }
        return {
            'data': data,
            'response': JsonResponse(data=data, status=400)
        }

    @staticmethod
    def _get_request_header(request, header):
        return request.META.get(header)

    def _get_system_request_headers(self, request):
        user = self._get_request_header(request, self.required_headers['user-auth'])
        if not user:
            return None, None, self._system_request_err()['response']

        token = self._get_request_header(request, self.required_headers['token-auth'])
        if not token:
            return None, None, self._system_request_err()['response']

        return user, token, None

    @staticmethod
    def _get_random_int(_min, _max, current=None):
        while True:
            rand = random.randint(_min, _max)
            if not current:
                return rand
            if rand != current:
                return rand

    def _get_random_stripped_uuid(self):
        uid = new_uuid()
        return uid[:self._get_random_int(25, len(uid))]

    @staticmethod
    def _parse_json(src):
        try:
            return json.loads(src), None
        except (json.JSONDecodeError, Exception) as err:
            err_msg = f'failed to parse payload as json. {_exc(err)}'
            _err(err_msg)
            return None, err_msg

    # warehouse
    def get_warehouse_list(self, request):
        user, err = self._get_system_request_user(request)
        if err:
            return err
        # noinspection PyUnresolvedReferences
        rows = Warehouse.objects.filter(user=user).filter(active=True)
        items = []
        for row in rows:
            _item = {
                'code': row.code,
                'name': row.name,
            }
            items.append(_item)
        result = {
            'count': len(items),
            'items': items,
        }
        return JsonResponse(result)

    def get_warehouse_list_help(self):
        result = {
            'description': 'get user warehouses list',
        }

        required_headers = [{header: 'header value'} for header in self.required_headers.keys()]
        request = {
            'method': 'GET',
            'path': f'/{self.get_api_full_path()}/warehouses/',
            'required_headers': required_headers,
        }
        items = [{'code': self._get_random_stripped_uuid(), 'name': f'warehouse_{i}'} for i in
                 range(1, 11)]

        response = {
            'count': len(items),
            'items': items,
        }

        result['request'] = request
        result['response_to_valid_request'] = {
            'response_status': 200,
            'response_body': response
        }
        result['response_to_invalid_request'] = {
            'response_status': 400,
            'response_body': self._system_request_err()['data']
        }
        return JsonResponse(data=result)

    # category
    def get_category_list(self, request):
        user, err = self._get_system_request_user(request)
        if err:
            return err
        # noinspection PyUnresolvedReferences
        rows = GoodsCategory.objects.filter(user=user)
        items = []
        for row in rows:
            _item = {
                'id': row.id,
                'name': row.name,
                'parent_id': row.parent.id if row.parent else None,
            }
            items.append(_item)
        result = {
            'count': len(items),
            'items': items,
        }
        return JsonResponse(result)

    @staticmethod
    def _append_to_dict(_dict, key, val):
        if stored_val := _dict[key] is None:
            return
        if isinstance(stored_val, int):
            _dict[key] += val
        elif isinstance(stored_val, set):
            _dict[key].add(val)
        elif isinstance(stored_val, bool):
            _dict[key] = val
        else:
            raise ValueError(
                f'The type {type(stored_val)} can not yet be handled by "_append_to_dict" method (api module)')

    # stock
    def update_stock(self, request):
        user, err = self._get_system_request_user(request)
        if err:
            return err

        # validate payload
        payload, err = self._parse_json(request.body)
        if err:
            return self._system_request_err(err)['response']

        # check if the required key is in payload
        key = 'offers'
        items = payload.get(key)
        if not items:
            err = f'"{key}" not found or empty'
            return self._system_request_err(err)['response']

        # check if items obj is iterable
        if not (items, Iterable):
            err = f'"{key}" object is not iterable (not an array/list/tuple)'
            return self._system_request_err(err)['response']

        # check items length against limit
        limit = self._update_stock_items_limit()
        if len(items) > limit:
            err = f'Number of "{key}" ({len(items)}) exceeds allowed limit ({limit})'
            return self._system_request_err(err)['response']

        # check if items have any duplicate sku
        skus = defaultdict(int)
        for item in items:
            if item_sku := item.get('sku'):
                skus[item_sku] += 1
        duplicates = [k for k, v in skus.items() if v > 1]
        if duplicates:
            err = f'items duplicated by sku found in "{key}": {",".join(duplicates)}'
            return self._system_request_err(err)['response']

        # read existing data from db
        # noinspection PyUnresolvedReferences
        goods_set = Good.objects.filter(user=user)
        goods = {item.sku: item for item in goods_set}

        # noinspection PyUnresolvedReferences
        brand_set = GoodsBrand.objects.filter(user=user)
        brands = {item.name.lower().strip(): item for item in brand_set}

        # noinspection PyUnresolvedReferences
        categories_set = GoodsCategory.objects.filter(user=user)
        cats = {item.id: item for item in categories_set}

        # noinspection PyUnresolvedReferences
        wh_set = Warehouse.objects.filter(user=user)
        whs = {item.code: item for item in wh_set}

        # noinspection PyUnresolvedReferences
        stock_qs = Stock.objects.filter(user=user)

        # process data
        stats = self._get_update_stock_stats()
        for item in items:
            if sku := item.get('sku') is None:
                self._append_to_dict(stats, 'invalid_goods', sku)
                continue

            # create a new good
            if good := goods.get(sku) is None:
                # TODO - create a new good, validate success, skip to next sku if error
                pass

            if stock := item.get('stock') is None:
                self._append_to_dict(stats, 'invalid_offers', sku)
                continue

            if not (stock, Iterable):
                self._append_to_dict(stats, 'invalid_offers', sku)
                continue

            # check for required keys in each stock obj
            required_keys = ('code', 'available')
            if not all(stock_dict.get(req_key) is not None for stock_dict in stock for req_key in required_keys):
                self._append_to_dict(stats, 'invalid_offers', sku)
                continue

            # check for wh code duplicates
            wh_codes = defaultdict(int)
            for stock_dict in stock:
                wh_codes[stock_dict.get('code')] += 1
            wh_duplicates = [k for k, v in wh_codes.items() if v > 1]
            if wh_duplicates:
                self._append_to_dict(stats, 'invalid_offers', sku)
                continue

            sku_stock_processing_success = True
            for stock_row in stock:
                wh_code = stock_row.get('code')
                available = stock_row.get('available')

                if wh := whs.get(wh_code) is None:
                    self._append_to_dict(stats, 'invalid_offers_rows', self._stock_row_as_str(sku, wh_code, available))
                    sku_stock_processing_success = False
                    continue

                # validate amount
                amount, err = self._int(available)
                if err:
                    self._append_to_dict(stats, 'invalid_offers_rows', self._stock_row_as_str(sku, wh_code, available))
                    sku_stock_processing_success = False
                    continue

                current_stock = stock_qs.filter(warehouse=wh).filter(good=good)
                data_to_update = self._stock_row_as_str(sku, wh_code, available)

                # update existing stock in db
                if len(current_stock):
                    delete_other_db_rows = True
                    for row_num, db_row in enumerate(current_stock, start=1):

                        # update stock for a single db row
                        if row_num == 1:
                            db_row.amount = amount
                            try:
                                db_row.save()
                                _log(
                                    f'Updated an existing db row with data: {data_to_update}')
                                self._append_to_dict(stats, 'processed_offers_rows', data_to_update)
                            except Exception as err:
                                err_msg = f'Failed to update an existing db row with data: {data_to_update}. ' \
                                          f'{_exc(err)}'
                                _err(err_msg)
                                self._append_to_dict(stats, 'failed_to_process_offers_rows', data_to_update)
                                sku_stock_processing_success = False
                                delete_other_db_rows = False
                            continue

                        # delete other rows if they exist and main db row was updated successfully
                        if delete_other_db_rows:
                            try:
                                db_row.delete()
                            except Exception as err:
                                err_msg = f'Failed to delete a redundant db row for warehouse code {wh_code} ' \
                                          f'and sku {sku}. {_exc(err)}'
                                _err(err_msg)
                                sku_stock_processing_success = False

                # add new row to db
                else:
                    new_db_row_data = {
                        'warehouse': wh,
                        'good': good,
                        'amount': amount,
                        'user': user,
                    }
                    new_db_row = Stock(**new_db_row_data)
                    try:
                        new_db_row.save()
                        _log(f'Added a new db row with data: {data_to_update}')
                        self._append_to_dict(stats, 'processed_offers_rows', data_to_update)
                    except Exception as err:
                        err_msg = f'Failed to add a new db row with data: {data_to_update}. {_exc(err)}'
                        _err(err_msg)
                        self._append_to_dict(stats, 'failed_to_process_offers_rows', data_to_update)
                        sku_stock_processing_success = False

            if sku_stock_processing_success:
                self._append_to_dict(stats, 'processed_offers', sku)

        processed_offers_count = len(stats['processed_offers'])
        success = bool(processed_offers_count)
        self._append_to_dict(stats, 'processed_offers_count', processed_offers_count)
        self._append_to_dict(stats, 'success', success)

        statuses = {
            True: 200,
            False: 400,
        }
        return JsonResponse(stats, status=statuses[success])

    @staticmethod
    def _update_stock_items_limit():
        return 250

    @staticmethod
    def _stock_row_as_str(sku, wh, amount):
        return f'{sku}: {wh} - {amount}'

    @staticmethod
    def _int(src):
        try:
            return int(src), None
        except (TypeError, Exception) as err:
            err_msg = f'Failed to parse an integer from "{src}". {_exc(err)}'
            _err(err_msg)
            return None, err_msg

    @staticmethod
    def _get_update_stock_stats():
        stats = {
            'created_goods': set(),
            'invalid_goods': set(),
            'failed_to_create_goods': set(),
            'processed_offers_rows': set(),
            'processed_offers': set(),
            'processed_offers_count': 0,
            'invalid_offers': set(),
            'invalid_offers_rows': set(),
            'failed_to_process_offers_rows': set(),
            'success': True,
        }
        return stats

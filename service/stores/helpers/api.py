import random
import json
from collections.abc import Iterable

from django.http import JsonResponse

from ..models import Warehouse
from ..models import GoodsCategory
from ..models import System
from .common import new_uuid
from .common import _exc
from .common import _err


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
            return None, self._get_invalid_system_request_response()['response']
        return system_rows[0].user, None

    @staticmethod
    def _get_invalid_system_request_response(reason=None):
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
            return None, None, self._get_invalid_system_request_response()['response']

        token = self._get_request_header(request, self.required_headers['token-auth'])
        if not token:
            return None, None, self._get_invalid_system_request_response()['response']

        return user, token, None

    @staticmethod
    def _get_random_int(min, max, current=None):
        while True:
            rand = random.randint(min, max)
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
            'response_body': self._get_invalid_system_request_response()['data']
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
        else:
            raise ValueError(f'The type {type(stored_val)} can not yet be handled by "_append_to_dict" method')

    # stock
    def update_stock(self, request):
        user, err = self._get_system_request_user(request)
        if err:
            return err

        # validate payload
        payload, err = self._parse_json()
        if err:
            return self._get_invalid_system_request_response(err)['response']

        key = 'offers'
        if items := payload.get() is None:
            err = f'no "{key}" object found in payload'
            return self._get_invalid_system_request_response(err)['response']

        if not (items, Iterable):
            err = f'"{key}" object is not iterable'
            return self._get_invalid_system_request_response(err)['response']

        # read existing rows from db

        # noinspection PyUnresolvedReferences
        goods_set = Good.objects.filter(user=user)
        goods = {item.sku: item for item in goods_set}

        # noinspection PyUnresolvedReferences
        brand_set = GoodsBrand.objects.filter(user=user)
        brands = {item.name.lower().strip(): item for item in brand_set}

        # noinspection PyUnresolvedReferences
        categories_set = GoodsCategory.objects.filter(user=user)
        cats = {item.name.lower().strip(): item for item in categories_set}

        # noinspection PyUnresolvedReferences
        wh_set = Warehouse.objects.filter(user=user)
        whs = {item.code: item for item in wh_set}

        # process data
        stats = {
            'created_goods': set(),
            'invalid_goods': set(),
            'failed_to_create_goods': set(),
            'successfully_processed_offers_count': 0,
            'invalid_offers': set(),
            'failed_to_process_offers': set(),
            'not_found_warehouses': set(),
        }

        # main loop to process items
        for item in items:
            if sku := item.get('sku') is None:
                self._append_to_dict(stats, 'invalid_goods', sku)
                continue

            if stock := item.get('stock') is None:
                self._append_to_dict(stats, 'invalid_offers', sku)
                continue

            if not isinstance(stock, dict):
                self._append_to_dict(stats, 'invalid_offers', sku)
                continue

            # TODO - create a new good
            if good := goods.get(sku) is None:
                pass

            for wh_code, amount in stock.items():
                if wh := whs.get(wh_code) is None:
                    self._append_to_dict(stats, 'invalid_offers', sku)
                    self._append_to_dict(stats, 'not_found_warehouses', wh_code)
                    continue

                # validate amoubt
                # update stock in db
                # update stats

        return JsonResponse(result)

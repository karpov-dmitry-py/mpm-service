import json
import random
import time
from collections import defaultdict
from typing import Dict, Any

import requests
from django.http import JsonResponse

from .common import _err
from .common import _exc
from .common import _log
from .common import new_uuid
from .common import time_tracker
from .common import to_float
from .managers import StockManager
from .managers import _get_user_qs
from ..models import Good
from ..models import GoodsBrand
from ..models import GoodsCategory
from ..models import Log
from ..models import LogRow
from ..models import Marketplace
from ..models import Stock
from ..models import Store
from ..models import StoreWarehouse
from ..models import System
from ..models import Warehouse
from ..models import now


# utils
def _parse_json(src):
    try:
        return json.loads(src), None
    except (json.JSONDecodeError, Exception) as err:
        err_msg = f'failed to parse payload as json. {_exc(err)}'
        _err(err_msg)
        return None, err_msg


def _parse_header(request, header):
    full_header = f'HTTP_{header.upper()}'
    val = request.META.get(full_header)
    if val is None or val == '':
        return None, f'"{header}" header not found or is empty in request'
    return val, None


def _handle_invalid_request(reason, status=400):
    data = {
        'invalid_request': True,
        'reason': reason,
    }
    response = JsonResponse(
        data=data,
        status=status,
        json_dumps_params={
            'ensure_ascii': False,
        })
    return \
        _get_response_decoded_body(response), \
        response


def _get_response_decoded_body(response):
    return response.content.decode(encoding='utf-8')


# noinspection PyUnresolvedReferences
def _get_marketplace_by_name(name):
    rows = Marketplace.objects.filter(name__icontains=name).order_by('id')
    if not rows:
        return
    return rows[0]


# class for api handling
class API:
    api_ver = '1'
    required_headers = {
        'user-auth': 'HTTP_USER_AUTH',
        'token-auth': 'HTTP_TOKEN_AUTH',
    }

    # help
    def get_api_help(self):
        general = [
            {'Общая информация': {
                'Актуальная версия': self.get_api_ver(),
                'Путь для запросов': f'/{self.get_api_full_path()}/'
            }
            },
            {'Авторизация': {
                'Способ авторизации': 'Передача данных для авторизации в заголовках запроса',
                "Заголовок <span class='code'>user-auth</span>": 'Email существующего пользователя сервиса (строка)',
                "Заголовок <span class='code'>token-auth</span>":
                    'Токен внешней системы, ранее добавленной в сервис в аккаунте '
                    'пользователя (строка)',
                'Описание': 'Сервис проверяет наличие и корректность авторизационных данных в заголовках запроса. '
                            'При не успешной авторизации (или при любом некорректном запросе) сервис вернет статус '
                            '<span class="code">400</span> и описание причины ошибочного запроса. '
                            'При успешной обработке запросе сервис вернет статус <span class="code">200</span>. '
                            'При ошибке сервиса будет возвращен статус <span class="code">500</span>. ',
            }
            }
        ]

        paths = [
            {'stock': {
                'method': 'POST',
                'path': f'{self.get_api_full_path()}/stock/',
                'what': '(товары и собственные остатки)',
                'title': f'Создание новых товаров и обновление собственных товарных остатков',
                'desc': f'Метод позволяет создавать новые товары и обновлять собственные товарные остатки на складах. '
                        f'За один запрос можно обновить данные по '
                        f'максимум {self._update_stock_items_limit()} товарам.<br> '
                        f'В запросе можно передать поля нового или существующего товара и список его остатков.<br>'
                        f'Минимально необходимые поля по товару для его создания в сервисе: '
                        f'<span class="code">sku</span> и <span class="code">name</span>.<br>'
                        f'Поиск бренда выполняется по наименованию. Регистр не важен. '
                        f'Если бренд не найден в сервисе, он создается и заполняется в карточке '
                        f'создаваемого товара.<br>'
                        f'Поиск категории выполняется по <span class="code">id</span>. '
                        f'Если категория не найдена, она остается пустой (null) в карточке создаваемого товара.<br>'
                        f'Поиск товара выполняется по полю <span class="code">sku</span>. '
                        f'Новый товар создается только при его отсутствии в сервисе. '
                        f'Поля существующего товара не обновляются.<br>'
                        f'Общий список по товарам <span class="code">offers</span> проверяется на дубли по товарам, '
                        f'на наличие идентификатора товара и списка его остатков.<br>'
                        f'Список остатков по товару <span class="code">stocks</span> проверяется на дубли по кодам '
                        f'складов, на наличие кода склада, на корректность '
                        f'кода склада, на целый не отрицательный остаток. '
                        f'Обновляются/добавляются только остатки, полученные в запросе. '
                        f'Остатки товара, имеющиеся в сервисе и не полученные в запросе, не обнуляются.<br>'
                        f'Обработка запроса считается успешной, если успешно обработаны все переданные остатки минимум '
                        f'одного товара из запроса. '
                        f'Статистика обработки запроса возвращается в ответе сервиса.',
                'request': [
                    {
                        'param': 'offers[]',
                        'type': 'array of serialized offers',
                        'desc': 'Список товаров и остатков',
                    },
                    {
                        'param': 'offers[][sku]',
                        'type': 'string',
                        'desc': 'Идентификатор товара',
                    },
                    {
                        'param': 'offers[][name]',
                        'type': 'string',
                        'desc': 'Наименование товара',
                    },
                    {
                        'param': 'offers[][brand]',
                        'type': 'string',
                        'desc': 'Бренд товара',
                    },
                    {
                        'param': 'offers[][category]',
                        'type': 'integer',
                        'desc': 'Идентификатор категории товара',
                    },
                    {
                        'param': 'offers[][description]',
                        'type': 'string',
                        'desc': 'Описание товара',
                    },
                    {
                        'param': 'offers[][article]',
                        'type': 'string',
                        'desc': 'Артикул товара',
                    },
                    {
                        'param': 'offers[][barcode]',
                        'type': 'string',
                        'desc': 'Штрихкод товара',
                    },
                    {
                        'param': 'offers[][weight]',
                        'type': 'float',
                        'desc': 'Вес товара (кг)',
                    },
                    {
                        'param': 'offers[][pack_width]',
                        'type': 'float',
                        'desc': 'Ширина упаковки товара (см)',
                    },
                    {
                        'param': 'offers[][pack_length]',
                        'type': 'float',
                        'desc': 'Длина упаковки товара (см)',
                    },
                    {
                        'param': 'offers[][pack_height]',
                        'type': 'float',
                        'desc': 'Высота упаковки товара (см)',
                    },
                    {
                        'param': 'offers[]stocks[]',
                        'type': 'array of serialized stocks',
                        'desc': 'Список остатков товара по складам',
                    },
                    {
                        'param': 'offers[]stocks[][code]',
                        'type': 'string',
                        'desc': 'Символьный код склада',
                    },
                    {
                        'param': 'offers[]stocks[][available]',
                        'type': 'integer',
                        'desc': 'Целый не отрицательный остаток товара на складе',
                    },
                ],
                'response': [
                    {
                        'param': 'created_goods[]',
                        'type': 'array of strings',
                        'desc': 'Список sku созданных товаров',
                    },
                    {
                        'param': 'invalid_goods[]',
                        'type': 'array of strings',
                        'desc': 'Список sku (или порядковых номеров предложений) с некорректными (или неполными) '
                                'данными для определения товара',
                    },
                    {
                        'param': 'failed_to_create_goods[]',
                        'type': 'array of strings',
                        'desc': 'Список sku товаров, которые не удалось создать',
                    },
                    {
                        'param': 'processed_offers_rows[]',
                        'type': 'array of strings',
                        'desc': 'Список успешно обработанных строк товарных остатков (строка содержит sku, '
                                'код склада и остаток',
                    },
                    {
                        'param': 'processed_offers',
                        'type': 'array of strings',
                        'desc': 'Список sku товаров, по которым полностью успешно обработаны все переданные остатки'
                    },
                    {
                        'param': 'processed_offers_count',
                        'type': 'integer',
                        'desc': 'Количество различных товаров, по которым полностью успешно обработаны все переданные '
                                'остатки'
                    },
                    {
                        'param': 'invalid_offers',
                        'type': 'array of strings',
                        'desc': 'Список sku товаров, по которым переданные остатки некорректны (неверный код склада и '
                                'др.)'
                    },
                    {
                        'param': 'invalid_offers_rows[]',
                        'type': 'array of strings',
                        'desc': 'Список некорректных строк товарных остатков (строка содержит sku, код склада и '
                                'остаток',
                    },
                    {
                        'param': 'failed_to_process_offers_rows[]',
                        'type': 'array of strings',
                        'desc': 'Список корректных строк товарных остатков, которые сервис не сумел обработать '
                                '(строка содержит sku, код склада и остаток',
                    },
                    {
                        'param': 'success',
                        'type': 'boolean',
                        'desc': 'Результат запроса (успешный/неуспешный). Успешный, если '
                                '<span class="code">processed_offers_count</span> > 0 (вне зависимости от кол-ва '
                                'созданных при обработке запроса товаров)',
                    },
                ]
            }
            },
            {'warehouses': {
                'method': 'GET',
                'path': f'{self.get_api_full_path()}/warehouses/',
                'what': '(список складов)',
                'title': f'Получение списка складов и их символьных кодов',
                'desc': 'Метод позволяет получить список складов и их символьных кодов (идентификаторов)',
                'response': [
                    {
                        'param': 'count',
                        'type': 'integer',
                        'desc': 'Количество объектов в ответе',
                    },
                    {
                        'param': 'items[]',
                        'type': 'array of serialized warehouses',
                        'desc': 'Список складов',
                    },
                    {
                        'param': 'items[][code]',
                        'type': 'string',
                        'desc': 'Символьный код склада',
                    },
                    {
                        'param': 'items[][name]',
                        'type': 'string',
                        'desc': 'Наименование склада',
                    }
                ]
            }
            },
            {'categories': {
                'method': 'GET',
                'path': f'{self.get_api_full_path()}/categories/',
                'what': '(список категорий)',
                'title': f'Получение списка товарных категорий и их идентификаторов',
                'desc': 'Метод позволяет получить список товарных категорий и их идентификаторов',
                'response': [
                    {
                        'param': 'count',
                        'type': 'integer',
                        'desc': 'Количество объектов в ответе',
                    },
                    {
                        'param': 'items[]',
                        'type': 'array of serialized categories',
                        'desc': 'Список товарных категорий',
                    },
                    {
                        'param': 'items[][id]',
                        'type': 'integer',
                        'desc': 'Идентификатор категории',
                    },
                    {
                        'param': 'items[][name]',
                        'type': 'string',
                        'desc': 'Наименование категории',
                    },
                    {
                        'param': 'items[][parent_id]',
                        'type': 'integer | null',
                        'desc': 'Идентификатор родительской категории (или null для категории верхнего уровня)',
                    },
                ]
            }
            },
        ]

        result = {
            'title': 'Описание API',
            'general': general,
            'paths': paths,
        }
        return result

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

    # noinspection PyTypeChecker
    def get_category_list_help(self):
        result = {
            'description': 'get user categories list',
        }

        required_headers = [{header: 'header value'} for header in self.required_headers.keys()]
        request = {
            'method': 'GET',
            'path': f'/{self.get_api_full_path()}/categories/',
            'required_headers': required_headers,

        }

        _min = 1
        _max = 10
        items = [{'id': i, 'name': f'category_{i}', 'parent_id': self._get_random_int(_min, _max, i)} for i in
                 range(_min, _max)]
        last = {
            'id': _max,
            'name': f'category_{_max} (no parent)',
            'parent_id': None,
        }
        items.append(last)

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

    # stock
    def update_stock(self, request):
        user, err = self._get_system_request_user(request)
        if err:
            return err

        # validate payload
        payload, err = _parse_json(request.body)
        if err:
            return self._system_request_err(err)['response']

        # check payload type
        if not isinstance(payload, dict):
            err = 'wrong type of payload, must be an object'
            return self._system_request_err(err)['response']

        # check if the required key is in payload
        key = 'offers'
        items = payload.get(key)
        if not items:
            err = f'"{key}" not found or empty'
            return self._system_request_err(err)['response']

        # check if items obj is iterable
        if not self._is_iterable(items):
            err = f'wrong type of "{key}", must be an array'
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

        db_data = {
            'brands': brands,
            'cats': cats,
        }

        # noinspection PyUnresolvedReferences
        wh_set = Warehouse.objects.filter(user=user)
        whs = {item.code: item for item in wh_set}

        # noinspection PyUnresolvedReferences
        stock_qs = Stock.objects.filter(user=user)

        # process payload
        stats = self._get_update_stock_stats()
        for item_index, item in enumerate(items):
            sku = item.get('sku')
            if not sku:
                self._append_to_dict(stats, 'invalid_goods', f'sku empty or not provided (offer # {item_index})')
                continue

            # create a new good
            good = goods.get(sku)
            if not good:
                good, validation_error, creation_error = self._create_good(item, db_data, user)

                if validation_error:
                    self._append_to_dict(stats, 'invalid_goods', {sku: validation_error})
                    continue

                if creation_error:
                    self._append_to_dict(stats, 'failed_to_create_goods', {sku: creation_error})
                    continue

                # a new good created successfully
                goods[sku] = good
                self._append_to_dict(stats, 'created_goods', sku)

            stocks = item.get('stocks')
            if not stocks:
                self._append_to_dict(stats, 'invalid_offers', sku)
                continue

            # check if stocks obj is iterable
            if not self._is_iterable(stocks):
                self._append_to_dict(stats, 'invalid_offers', sku)
                continue

            # check for required keys in each stock obj
            required_keys = ('code', 'available')
            if not all(stock_dict.get(req_key) is not None for stock_dict in stocks for req_key in required_keys):
                self._append_to_dict(stats, 'invalid_offers', sku)
                continue

            # check for warehouse code duplicates
            wh_codes = defaultdict(int)
            for stock_dict in stocks:
                wh_codes[stock_dict.get('code')] += 1
            wh_duplicates = [k for k, v in wh_codes.items() if v > 1]
            if wh_duplicates:
                self._append_to_dict(stats, 'invalid_offers', sku)
                continue

            sku_stock_processing_success = True
            for stock in stocks:
                wh_code = stock.get('code')
                available = stock.get('available')
                data_to_update = self._stock_row(sku, wh_code, available)

                wh = whs.get(wh_code)
                if not wh:
                    self._append_to_dict(stats, 'invalid_offers_rows', data_to_update)
                    sku_stock_processing_success = False
                    continue

                # validate amount
                amount, err = self._int(available)
                if err:
                    self._append_to_dict(stats, 'invalid_offers_rows', data_to_update)
                    sku_stock_processing_success = False
                    continue

                if amount < 0:
                    self._append_to_dict(stats, 'invalid_offers_rows', data_to_update)
                    sku_stock_processing_success = False
                    continue

                current_stock = stock_qs.filter(warehouse=wh).filter(good=good)
                # update existing stock in db
                if len(current_stock):
                    delete_other_db_rows = True
                    for row_num, db_row in enumerate(current_stock, start=1):

                        # update stock for a single db row
                        if row_num == 1:
                            db_row.amount = amount
                            try:
                                db_row.save()
                                _log(f'Updated an existing db row with data: {data_to_update}')
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

        # status
        error_states = ('failed_to_create_goods', 'failed_to_process_offers_rows',)
        if any(stats[state] for state in error_states):
            status = 500
        elif success:
            status = 200
        else:
            status = 400
        self._prepare_dict(stats)
        return JsonResponse(data=stats, status=status, safe=False)

    @staticmethod
    def _is_iterable(obj):
        types = (list, tuple, set)
        return type(obj) in types

    def _create_good(self, src: Dict[Any, str], db_data: Dict[str, dict], user: Any):
        """
        Return a created Good instance (or None if there is a validation or creation error),
        validation error, creation error (or None as an error if there isn't any)
        """
        brands = db_data.get('brands')
        cats = db_data.get('cats')
        required_fields = ('sku', 'name')
        try:
            cleaned_data = {field: str(src.get(field)).strip() for field in required_fields if src.get(field)}
        except Exception as err:
            err_msg = f'Failed to convert required fields to strings to ' \
                      f'create a new good ({", ".join(required_fields)}). {_exc(err)}'
            _err(err_msg)
            return None, err_msg, None

        if not all(field in cleaned_data for field in required_fields):
            err_msg = f'Not all mandatory fields provided to create a new good ({", ".join(required_fields)})'
            _log(err_msg)
            return None, err_msg, None

        # user
        cleaned_data['user'] = user

        # article, description, barcode
        char_fields = ('article', 'description', 'barcode',)
        char_fields_dict = {field: str(src.get(field)).strip() for field in char_fields if src.get(field)}
        cleaned_data.update(char_fields_dict)

        # brand
        raw_brand = src.get('brand')
        if raw_brand:
            brand = str(raw_brand).strip()
            search_brand = brand.lower()
            brand_ref = brands.get(search_brand)
            if brand_ref:
                cleaned_data['brand'] = brand_ref
            else:
                new_brand = GoodsBrand(name=brand, user=user)
                try:
                    new_brand.save()
                    _log(f'A new brand created: "{brand}"')
                    brands[search_brand] = new_brand
                    cleaned_data['brand'] = new_brand
                except Exception as err:
                    err_msg = f'Failed to create a new brand: "{brand}": {_exc(err)}'
                    _err(err_msg)

        # category
        raw_cat = src.get('category')
        if raw_cat:
            cat_id, err = self._int(raw_cat)
            if cat_id is not None:
                if category_ref := cats.get(cat_id):
                    cleaned_data['category'] = category_ref

        float_fields = ('weight', 'pack_width', 'pack_length', 'pack_height',)
        float_fields_dict = {field: to_float(src.get(field)) for field in float_fields if
                             to_float(src.get(field)) is not None}
        cleaned_data.update(float_fields_dict)

        new_good = Good(**cleaned_data)
        try:
            new_good.save()
            _log(f'A new good created: "{new_good}"')
            return new_good, None, None
        except Exception as err:
            err_msg = f'Failed to create a new good: "{new_good}": {_exc(err)}'
            _err(err_msg)
            return None, None, err_msg

    @staticmethod
    def _append_to_dict(_dict, key, val):
        stored_val = _dict[key]
        if stored_val is None:
            return
        if isinstance(stored_val, bool):
            _dict[key] = val
        elif isinstance(stored_val, set):
            _dict[key].add(f'{val}')
        elif isinstance(stored_val, int):
            _dict[key] += val
        else:
            raise ValueError(
                f'The type {type(stored_val)} can not yet be handled by "_append_to_dict" method (api module)')

    @staticmethod
    def _prepare_dict(_dict):
        for k, v in _dict.items():
            if isinstance(v, set):
                _dict[k] = list(v)

    @staticmethod
    def _update_stock_items_limit():
        return 250

    @staticmethod
    def _stock_row(sku, wh, amount):
        return {
            'sku': sku,
            'warehouse': wh,
            'available': amount,
        }

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


# class for logging stock and price export events to db and also reading data from these logs
class Logger:
    ok_statuses = (200, 201, 204, 301, 302,)

    def log(self, _dict):
        try:
            marketplace = _dict.get('marketplace')
            status = _dict.get('response_status', 200)
            log = Log(
                marketplace=marketplace,
                store=_dict.get('store'),
                warehouse=_dict.get('warehouse'),
                duration=time.time() - _dict.get('start_time', time.time()),
                request=_dict.get('request'),
                response=_dict.get('response'),
                response_status=status,
                success=_dict.get('success', status in self.ok_statuses),
                error=_dict.get('error'),
                comment=_dict.get('comment'),
                user=_dict.get('user')
            )
            log.save()
            _log(f'saved a log row to db for marketplace {marketplace}.')
            return log, None
        except (OSError, Exception) as err:
            err_msg = f'failed to save a log to db: {_exc(err)}'
            _err(err_msg)
            return None, err_msg

    @staticmethod
    def update_log(log, _dict):
        try:
            for k, v in _dict.items():
                key = k
                val = v
                if k == 'start_time':
                    key = 'duration'
                    val = time.time() - _dict.get('start_time', time.time())
                setattr(log, key, val)
            log.save()
            _log('updated a log in db')
            return log, None
        except (OSError, Exception) as err:
            err_msg = f'failed to update a log in db: {_exc(err)}'
            _err(err_msg)
            return None, err_msg

    @staticmethod
    def _get_goods_qs_by_skus(skus, user):
        qs = _get_user_qs(Good, user).filter(sku__in=skus)
        _dict = {item.sku: item for item in qs}
        return _dict

    # noinspection PyUnresolvedReferences
    def log_rows(self, log, stock):
        user = log.user
        goods = self._get_goods_qs_by_skus(list(stock.keys()), user)
        rows = []
        for sku, _dict in stock.items():
            amount = _dict.get('amount', 0)
            success = _dict.get('success', True)
            err_code = _dict.get('err_code', None)
            err_msg = _dict.get('err_msg', None)

            row = LogRow(
                log=log,
                good=goods.get(sku),
                sku=sku,
                amount=amount,
                success=success,
                err_code=err_code,
                err_msg=err_msg,
            )
            rows.append(row)
        try:
            LogRow.objects.bulk_create(rows)
            _log(f'saved log rows to db: {len(rows)}')
        except (OSError, Exception) as err:
            err_msg = f'failed to save log rows ({len(rows)}) to db: {_exc(err)}'
            _err(err_msg)
            return err_msg


# class for communication with yandex market via api
class YandexApi:
    stock_type = 'FIT'
    auth_header = 'Authorization'
    marketplace_name = 'yandex'

    def __init__(self):
        pass

    # noinspection PyUnresolvedReferences
    @time_tracker('yandex_update_stock')
    def update_stock(self, request, store_pk):
        logger = Logger()
        status_code = 400
        start_time = time.time()
        log = {
            'start_time': start_time,
            'request': request.body.decode(),
            'marketplace': _get_marketplace_by_name(self.marketplace_name),
        }
        qs = Store.objects.filter(id=store_pk)
        if not qs:
            err = f'no store with id "{store_pk}" found in database'
            resp_payload, response = _handle_invalid_request(err)
            log['response'], log['response_status'], log['error'] = resp_payload, status_code, err
            logger.log(log)
            return response

        store = qs[0]
        log['store'] = store

        user = store.user
        log['user'] = user

        # parse auth header
        auth_header_val, err = _parse_header(request, self.auth_header)
        if err:
            status_code = 403
            resp_payload, response = _handle_invalid_request(err, status_code)
            log['response'], log['response_status'], log['error'] = resp_payload, status_code, err
            logger.log(log)
            return response

        # validate auth header
        err = self._validate_auth_header_val(store, auth_header_val)
        if err:
            status_code = 403
            resp_payload, response = _handle_invalid_request(err, status_code)
            log['response'], log['response_status'], log['error'] = resp_payload, status_code, err
            logger.log(log)
            return response

        payload, err = _parse_json(request.body)
        if err:
            resp_payload, response = _handle_invalid_request(err)
            log['response'], log['response_status'], log['error'] = resp_payload, status_code, err
            logger.log(log)
            return response

        # parse warehouse
        wh, yandex_wh_id, err = self._get_wh_from_stock_update_request(payload, store)
        if err:
            resp_payload, response = _handle_invalid_request(err)
            log['response'], log['response_status'], log['error'] = resp_payload, status_code, err
            logger.log(log)
            return response

        log['warehouse'] = wh
        skus = payload.get('skus')
        stocks = StockManager().calculate_stock_for_skus(wh.user, skus, wh.id, False)

        stock = {sku: stocks[sku][0]['amount'] if sku in stocks else 0 for sku in skus}  # all skus are in this dict
        skus_stock = []
        _now = now()

        for sku in skus:
            row = {
                'sku': sku,
                'warehouseId': yandex_wh_id,
                'items': [
                    {
                        'type': self.stock_type,
                        'count': stock[sku],
                        'updatedAt': _now,
                    },
                ],
            }
            skus_stock.append(row)

        result = {
            'skus': skus_stock,
        }
        response = self._make_response(data=result)
        log['response'] = _get_response_decoded_body(response)
        log, err = logger.log(log)
        if err:
            return response  # failed to save log to db, let's return result

        stock = {sku: {'amount': amount} for sku, amount in stock.items()}
        logger.log_rows(log, stock)
        logger.update_log(log, {'start_time': start_time})

        return response

    @staticmethod
    def _make_response(data, status=200):
        return JsonResponse(
            data=data,
            safe=False,
            status=status,
            json_dumps_params={
                'indent': 4,
                'ensure_ascii': False,
            })

    def _validate_auth_header_val(self, store, header_val):
        prop_name = 'store_api_auth_token'
        prop_val = store.get_prop(prop_name=prop_name)

        if not prop_val:
            _log(f'WARNING! store prop "{prop_name}" for store with id "{store.id}" not found in database!')
            return None

        if prop_val.lower().strip() != header_val.lower().strip():
            return f'"{self.auth_header}" header has value "{header_val}" that does not match store ' \
                   f'with id "{store.id}"'

    # noinspection PyUnresolvedReferences
    @staticmethod
    def _get_wh_from_stock_update_request(payload, store):
        """
        payload validation
        """
        # check wh id
        wh_id_attrs = ('partnerWarehouseId', 'warehouseId',)
        if not any(attr in payload for attr in wh_id_attrs):
            return None, None, 'no warehouse id found in payload'

        if all(not payload.get(attr) for attr in wh_id_attrs):
            return None, None, 'no valid warehouse id found in payload'

        # get wh id
        wh_id = payload.get(wh_id_attrs[0])
        yandex_wh_id = payload.get(wh_id_attrs[1])

        if yandex_wh_id is None:
            return None, None, 'no valid yandex native warehouse id found in payload'

        # check whether wh id is in db
        qs = StoreWarehouse.objects.filter(code=str(wh_id))
        if not qs:
            return None, None, f'no warehouse with id "{wh_id}" found in database'

        wh = qs[0]
        if wh.store != store:
            return None, None, f'no warehouse with id "{wh_id}" found for store with id "{store_pk}" in database'

        # check skus list
        skus = 'skus'
        if skus not in payload:
            return None, None, f'no "{skus}" list found in payload'

        skus_vals = payload.get(skus)
        if type(skus_vals) not in (list, tuple):
            return None, None, f'invalid type of "{skus}" found in payload, must be iterable'

        if not skus_vals:
            return None, None, f'empty "{skus}" list found in payload'

        if all(not item for item in skus_vals):
            return None, None, f'all of skus are empty in "{skus}" in payload'

        return wh, yandex_wh_id, None


# class for communication with ozon via api
class OzonApi:
    marketplace_name = 'ozon'
    stock_update_batch_size = 100
    ok_statuses = (200, 201, 204, 301, 302, 304,)
    api_base_url = 'https://api-seller.ozon.ru/v2'

    def __init__(self):
        self._session = requests.Session()
        self._logger = Logger()
        self._errors = []

    def _log(self, msg):
        return self._logger.log(msg)

    @staticmethod
    def _resp_ok(status):
        return status in OzonApi.ok_statuses

    def _post(self, url, _json=None):
        if _json is None:
            response = self._session.post(url)
        else:
            response = self._session.post(url, json=_json)

        status = response.status_code
        if self._resp_ok(status):
            return response.json(), status, None

        return None, status, response.text

    def _get_seller_stock(self, store):
        result_key = 'result'
        items_key = 'items'
        sku_key = 'offer_id'
        sku_stocks_key = 'stocks'
        sku_stock_type_key = 'type'
        sku_reserved_stock_key = 'reserved'

        target_url = f'{self.api_base_url}/product/info/stocks'
        query_page_size = int(2 ** 32 / 2) - 1
        # query_page_size = 50
        query_page_num = 0

        base_err = f'В ответе от api маркетплейса ({target_url})'
        key_not_found_err = f'{base_err} не найдено значение по ключу'

        store_type = store.store_type.name.lower().strip()
        stocks = dict()

        payload = dict(page_size=query_page_size, page=query_page_num)
        resp_payload, _, err = self._post(target_url, _json=payload)
        if err:
            return None, err

        result = resp_payload.get(result_key)
        if result is None:
            return None, f'{key_not_found_err} "{result_key}"'

        items = result.get(items_key)
        if items is None:
            return None, f'{key_not_found_err} "{items_key}"'

        if not len(items):
            return stocks, None

        for item in items:

            sku = item.get(sku_key)
            if sku is None:
                return None, f'{key_not_found_err} "{sku_key}"'

            sku_stocks = item.get(sku_stocks_key)
            if sku_stocks is None:
                return None, f'{key_not_found_err} "{sku_stocks_key}"'

            sku_total_reserved = 0
            store_type_has_sku_stock = False
            for stock in sku_stocks:

                stock_type = stock.get(sku_stock_type_key)
                if stock_type is None:
                    return None, f'{key_not_found_err} "{sku_stock_type_key}"'

                if stock_type.strip().lower() == store_type:
                    reserved = stock.get(sku_reserved_stock_key)
                    if reserved is None:
                        return None, f'{key_not_found_err} "{sku_reserved_stock_key}"'

                    sku_total_reserved += reserved
                    store_type_has_sku_stock = True

            if not store_type_has_sku_stock:
                return None, f'{base_err} нет остатка товара {sku} для типа магазина {store_type}'

            stocks[sku] = sku_total_reserved

        return stocks, None

    @staticmethod
    def _json(val):
        return json.dumps(val, indent=4, ensure_ascii=False)

    def _update_stock(self, wh, skus):
        target_url = f'{self.api_base_url}/products/stocks'
        rows = []
        start_time = time.time()
        log = {
            'start_time': start_time,
            'marketplace': wh.store.marketplace,
            'store': wh.store,
            'warehouse': wh,
            'user': wh.user,
        }

        wh_code = wh.code
        for _dict in skus:
            for sku, amount in _dict.items():
                row = {'offer_id': sku, 'stock': amount, 'warehouse_id': wh_code}
                rows.append(row)
        payload = {'stocks': rows}
        log['request'] = self._json(payload)

        resp_payload, status, err = self._post(url=target_url, _json=payload)
        log['response_status'] = status
        log['response'] = self._json(resp_payload)

        if err:
            log['response'] = err
            err = f'Ошибочный ответ от api маркетплейса {target_url}\n, статус: {status}\n, ' \
                  f'текст ответа:\n {err}'
            self._errors.append(err)
            log['error'] = err

            _, err = self._log(log)
            if err:
                self._errors.append(err)
            return

        log, err = self._log(log)
        if err:
            self._errors.append(err)

        # todo - append skus detailed rows to log
        skus, err = self._handle_stock_update_response(resp_payload, skus, target_url)
        if err:
            self._errors.append(err)
            return

        self._logger.log_rows(log, skus)
        self._logger.update_log(log, {'start_time': start_time})

    @staticmethod
    def _handle_stock_update_response(payload, stocks, target_url):
        result_key = 'result'
        sku_key = 'offer_id'
        updated_key = 'updated'
        errors_key = 'errors'
        err_code_key = 'code'
        err_msg_key = 'message'

        base_err = f'В ответе от api маркетплейса ({target_url})'
        key_not_found_err = f'{base_err} не найдено значение по ключу'

        _stocks = dict()
        for _dict in stocks:
            for sku, amount in _dict.items():
                _stocks[sku] = amount

        items = payload.get(result_key)
        if items is None:
            return None, f'{key_not_found_err} "{result_key}"'

        skus = dict()
        for item in items:

            sku = item.get(sku_key)
            if sku is None:
                return None, f'{key_not_found_err} "{sku_key}"'

            is_updated = item.get(updated_key)
            if is_updated is None:
                return None, f'{key_not_found_err} "{updated_key}"'

            sku_data = {
                'amount': _stocks.get(sku, 0),
                'success': is_updated,
            }

            errors = item.get(errors_key)
            if errors is None:
                return None, f'{key_not_found_err} "{errors_key}"'

            err_codes = dict()
            err_msgs = dict()
            for err in errors:

                err_code = err.get(err_code_key)
                if err_code is None:
                    return None, f'{key_not_found_err} "{err_code_key}"'
                err_codes[err_code] = True

                err_msg = err.get(err_msg_key)
                if err_msg is None:
                    return None, f'{key_not_found_err} "{err_msg_key}"'
                err_msgs[err_msg] = True

            err_codes_all = ', '.join(list(err_codes.keys()))
            err_msgs_all = ', '.join(list(err_msgs.keys()))

            sku_data['err_code'] = err_codes_all
            sku_data['err_msg'] = err_msgs_all

            skus[sku] = sku_data

        return skus, None

    def _set_auth_headers(self, store):
        headers = {
            'Client-Id': None,
            'Api-Key': None,
        }

        for k in headers:
            headers[k] = store.get_prop(prop_name=k)

        missing_headers = [k for k, v in headers.items() if v is None]
        if len(missing_headers):
            return f'В карточке магазина "{store.name}" введены не все обязательные поля для работы с ' \
                   f'api маркетплейса: {", ".join(missing_headers)}'

        self._session.headers.update(headers)

    @staticmethod
    def _merge_stocks(seller_stocks, db_stocks):
        for sku in list(seller_stocks.keys()):
            db_stock = db_stocks.get(sku)
            if db_stock is None:
                seller_stocks[sku] = 0
                continue

            reserved = seller_stocks.get(sku, 0)
            seller_stocks[sku] = max(0, db_stock - reserved)
            db_stocks.pop(sku)

        # merge remaining skus from db stocks
        for sku, db_stock in db_stocks.items():
            seller_stocks[sku] = db_stock

    def update_stock(self, wh):
        # todo - set limit 80 requests per minute !!!

        store = wh.store
        err = self._set_auth_headers(store)
        if err:
            return err

        seller_stocks, err = self._get_seller_stock(store)
        if err:
            return err

        db_stocks = StockManager().calculate_stock_for_skus(wh.user, None, wh.id, False)
        if not len(db_stocks):
            err = f'Нет доступных остатков (с учетом правил доступности остатков) по складу магазина "{wh.name}"'
            return err

        db_stocks = {sku: _list[0]['amount'] for sku, _list in db_stocks.items()}
        self._merge_stocks(seller_stocks, db_stocks)
        stocks_list = [{sku: stock} for sku, stock in seller_stocks.items()]

        slices = []
        while len(stocks_list) > 0:
            _slice = stocks_list[:self.stock_update_batch_size]
            slices.append(_slice)
            stocks_list = stocks_list[self.stock_update_batch_size:]

        _log(f'total slices: {len(slices)}')

        for _slice in slices:
            self._update_stock(wh, _slice)

        if len(self._errors):
            return '. '.join(self._errors)

import random
import json
from collections import defaultdict
from collections.abc import Iterable
from typing import Dict, Any

from django.http import JsonResponse

from ..models import Warehouse
from ..models import GoodsCategory
from ..models import GoodsBrand
from ..models import Good
from ..models import System
from ..models import Stock

from .common import new_uuid
from .common import to_float
from .common import _exc
from .common import _err
from .common import _log


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
                "Заголовок <span class='code'>token-auth</span>": 'Токен внешней системы, ранее добавленной в сервис в аккаунте '
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
                        f'За один запрос можно обновить данные по максимум {self._update_stock_items_limit()} товарам. '
                        f'В запросе можно передать поля нового или существующего товара и список его остатков.'
                        f'Минимально необходимые поля по товару для его создания в сервисе: '
                        f'<span class="code">sku</span> и <span class="code">name</span>. '
                        f'Поиск бренда выполняется по наименованию. Регистр не важен. '
                        f'Поиск категории выполняется по <span class="code">id</span>. '
                        f'Если бренд не найден в сервисе, он создается и заполняется в карточке создаваемого товара. '
                        f'Если категория не найдена, она остается пустой (null) в карточке создаваемого товара. '
                        f'Поиск товара выполняется по полю <span class="code">sku</span>. '
                        f'Новый товар создается только при его отсутствии в сервисе. '
                        f'Существующий товар не обновляется. '
                        f'Общий список по товарам <span class="code">offers</span> проверяется на дубли по товарам, '
                        f'на наличие идентификатора товара и списка его остатков. '
                        f'Список остатков по товару <span class="code">stocks</span> проверяется на дубли по кодам '
                        f'складов, на наличие кода склада, на корректность '
                        f'кода склада, на целый не отрицательный остаток. '
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
                        'type': 'integer',
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
                        'desc': 'Список успешно обработанных строк товарных остатков (строка содержит sku, код склада и '
                                'остаток',
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
        payload, err = self._parse_json(request.body)
        if err:
            return self._system_request_err(err)['response']

        # check payload type
        if not isinstance(payload, dict):
            err = 'payload has the wrong type, must be an object'
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

            if not (stocks, Iterable):
                self._append_to_dict(stats, 'invalid_offers', sku)
                continue

            # check for required keys in each stock obj
            required_keys = ('code', 'available')
            if not all(stock_dict.get(req_key) is not None for stock_dict in stocks for req_key in required_keys):
                self._append_to_dict(stats, 'invalid_offers', sku)
                continue

            # check for wh code duplicates
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

import datetime

import requests
from bs4 import BeautifulSoup

from threading import Lock
from concurrent.futures import ThreadPoolExecutor

from .common import parse_int
from .common import get_duration
from .common import _log
from .common import _err

cyrillics = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'


class Parser:
    supplier_base_url = 'https://neotren.ru'
    supplier = supplier_base_url.split('//')[1]
    own_stock_url = 'https://sportpremier.ru/bitrix/catalog_export/yandex_all.php'
    own_stock_is_required = True
    search_result_count = 10 ** 6
    availability = {
        'true': True,
        'false': False,
        True: 'В наличии',
        False: 'Не в наличии',
    }

    def __init__(self):
        self._mutex = Lock()
        self._rows = dict()
        self._own_stock = dict()
        self._error = None
        self._cats = self._get_categories()

    @staticmethod
    def _get_categories():
        result = {
            '569': {
                'name': 'Беговые дорожки',
                'own_cat_id': '3',
            },
            '573': {
                'name': 'Велотренажеры',
                'own_cat_id': '12',
            },
            '577': {
                'name': 'Эллиптические тренажеры',
                'own_cat_id': '21',
            },
            '581': {
                'name': 'Степперы и эскалаторы',
                'own_cat_id': '35',
            },
            '584': {
                'name': 'Гребные тренажеры',
                'own_cat_id': '30',
            },
            '592': {
                'name': 'Силовые тренажеры',
                'own_cat_id': '47',
            },
        }

        for k in result.keys():
            result[k]['own_cats'] = []

        return result

    @staticmethod
    def get_supplier_categories():
        return {k: v['name'] for k, v in Parser._get_categories().items()}

    def _get_own_stock(self, category_ids):
        url = self.own_stock_url
        response = requests.get(url, timeout=60)
        if response.status_code != 200:
            error = f'failed to download src xml file, response status: {response.status_code}, ' \
                    f'response text: {response.text}'
            _err(error)
            return error

        soup = BeautifulSoup(response.text, 'lxml')
        stock = soup.find_all('offer')
        if not len(stock):
            return f'Не найдены остатки по источнику {url}'

        goods = dict()
        for row in stock:
            good = {'is_on_supplier_site': False}
            good_url = row.find('url')
            if good_url is None:
                _log('Нет тега "url" в предложении по собственным остаткам')
                continue

            # name
            name = row.find('url')
            if name is not None:
                good['name'] = name.text

            # is_available
            is_available = row.attrs.get_by_code('available', 'false')
            good['available'] = self.availability.get(is_available, False)

            goods[good_url.text] = good

        if not len(goods):
            return f'Найдены пустые остатки (нет тега "url") по источнику {url}'

        # parse categories
        cats_soup = soup.find_all('category')
        cats, err = self._parse_own_categories(cats_soup, url)
        if err:
            return err

        self._own_stock = {
            'cats': cats,
            'goods': goods,
        }

    @staticmethod
    def _parse_own_categories(cats, url):
        if not cats:
            return None, f'Не найдены категории товаров по источнику {url}'
        parsed_cats = dict()
        for cat in cats:
            pass

        return parsed_cats, None

    def get_suppliers_offers(self, category_ids):
        start = datetime.datetime.now()

        err = self._get_own_stock(category_ids)
        if err and self.own_stock_is_required:
            return None, err

        with ThreadPoolExecutor(max_workers=min(len(category_ids), 50)) as executor:
            for cat_id in category_ids:
                executor.submit(self._get_supplier_category_offers, category_id=cat_id)

        if self._error:
            return None, self._error

        with ThreadPoolExecutor(max_workers=min(len(self._rows), 50)) as executor:
            for name in self._rows:
                executor.submit(self.check_item, name=name)

        price_diff_count = 0
        stock_diff_count = 0
        error_count = 0

        for name, props in self._rows.items():

            has_price_diff = props.get_by_code('price') != props.get_by_code('own_price')
            props['has_price_diff'] = has_price_diff
            if has_price_diff:
                price_diff_count += 1

            has_stock_diff = not self._stock_matches(props.get_by_code('stock', ''), props.get_by_code('own_stock', ''))
            props['has_stock_diff'] = has_stock_diff
            if has_stock_diff:
                stock_diff_count += 1

            if props.get_by_code('error'):
                error_count += 1

        return {
                   'duration': get_duration(start),
                   'supplier': self.supplier,
                   'supplier_url': self.supplier_base_url,
                   'rows': self._rows,
                   'price_diff_count': price_diff_count if price_diff_count > 0 else None,
                   'stock_diff_count': stock_diff_count if stock_diff_count > 0 else None,
                   'error_count': error_count if error_count > 0 else None,
                   'own_stock_url': self.own_stock_url,
               }, None

    def _get_supplier_category_offers(self, category_id):
        category_url = f'{self.supplier_base_url}/catalog?category={category_id}'
        target_url = f'{category_url}&limit={self.search_result_count}'

        response = requests.get(url=target_url, timeout=60)
        status = response.status_code
        if status != 200:
            return None, f'Ошибка при получении данных с сайта поставщика: {target_url}, код ответа: {status}, ' \
                         f'текст ответа: {response.text}'

        soup = BeautifulSoup(response.text, 'lxml')
        items = soup.find_all('table', class_='prodinfo')

        # parse supplier site
        for item in items:
            name = ''
            props = {
                'error': '',
                'category': self._cats.get(category_id, dict()).get('name', ''),
                'category_url': category_url,
            }

            # name and url
            href_name = item.find('a')
            if href_name is not None:
                name = href_name.text
                props['good_name'] = name
                props['good_url'] = f'{self.supplier_base_url}{href_name.attrs.get_by_code("href")}'

            # price
            price = item.find('span', class_='productPrice')
            if price is not None:
                price, err = parse_int(price.text)
                if price is not None:
                    props['price'] = price

            # stock
            stock, err = self._parse_stock(item)
            if stock is not None:
                props['stock'] = stock

            if name:
                with self._mutex:
                    self._rows[name] = props

        if not len(self._rows):
            self._error = f'Не найдены товары на сайте поставщика: {target_url}'

    def check_item(self, name):
        """
        check item on own site
        """
        cleaned_name = ''.join([char for char in name.lower() if char not in cyrillics]).strip()
        if not cleaned_name:
            with self._mutex:
                self._rows[name]['error'] = f'Сформирована пустая строка поиска для товара "{name}"'
            return

        self_stock = self._own_stock.get('goods', {})
        self_base_url = 'https://sportpremier.ru'
        target_url = f'{self_base_url}/search/?q={cleaned_name}'

        _log(f'searching own site for "{cleaned_name} ..."')
        response = requests.get(target_url, timeout=120)
        if response.status_code != 200:
            with self._mutex:
                self._rows[name]['error'] = f'Ошибка поиска товара "{cleaned_name}" на сайте {self_base_url}: ' \
                                            f'({response.status_code}) {response.text}'
            return

        soup = BeautifulSoup(response.text, 'lxml')
        items = soup.find_all('div', class_='item')
        if items is None or not len(items):
            with self._mutex:
                self._rows[name]['error'] = f'Пустой результат поиска товара "{cleaned_name}" на сайте {self_base_url}'
            return

        item = items[0]
        props = dict()

        name_div = item.find('div', class_='title')
        if name_div is not None:
            name_href = name_div.find('a')
            if name_href is not None:
                searched_path = name_href.attrs.get_by_code("href", '').split('?sphrase_id=')[0]
                props['url'] = f'{self_base_url}{searched_path}'
                props['name'] = name_href.text

        if not len(props):
            with self._mutex:
                self._rows[name]['error'] = f'Не удалось распарсить наименование и ссылку на товар "{cleaned_name}" ' \
                                            f'на сайте {self_base_url}'
            return

        price_div = item.find('div', class_='price')
        if price_div is not None:
            price = price_div.text
            price_val, err = parse_int(price)
            if err:
                with self._mutex:
                    self._rows[name]['error'] = f'Не удалось распарсить цену на товар "{cleaned_name}" ' \
                                                f'на сайте {self_base_url}'
                return

            props['price'] = price_val

        if props.get('price') is None:
            with self._mutex:
                self._rows[name]['error'] = f'Не удалось распарсить цену на товар "{cleaned_name}" ' \
                                            f'на сайте {self_base_url}'
            return

        url = props.get('url')
        good = self_stock.get(url)
        if good is not None:
            self_stock[url]['is_on_supplier_site'] = True

        if good is None or not good.get('available', False):
            props['stock'] = self.availability[False]
        else:
            props['stock'] = self.availability[True]

        with self._mutex:
            item_props = self._rows[name]
            for k, v in props.items():
                item_props[f'own_{k}'] = v
            self._rows[name] = item_props

    @staticmethod
    def _stock_matches(pivot, other):
        available = 'в наличии'
        if (pivot.strip().lower() == available or other.strip().lower() == available) \
                and pivot.strip().lower() != other.strip().lower():
            return False
        return True

    @staticmethod
    def _parse_stock(item_soup):
        default_val = 'Не удалось получить значение'

        stock = item_soup.find('span', class_='region')
        if stock is None:
            return default_val, None

        stock_val = ''

        # parse as <p>
        stock_p = stock.find('p')
        if stock_p is not None:
            stock_val = stock_p.text

        # parse as <div>
        if not stock_val:
            stock_div = stock.find('div', class_='color-box')
            if stock_div is not None:
                stock_val = stock_div.text

        if not stock_val:
            return default_val, None

        return stock_val.strip(), None

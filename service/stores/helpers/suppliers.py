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
    own_stock_is_required = True
    search_result_count = 2  # 10**6

    def __init__(self):
        self._mutex = Lock()
        self._rows = dict()
        self._error = None
        self._cats = self.get_categories()
        self._own_stock = None

    @staticmethod
    def get_categories():
        result = {
            '569': 'Беговые дорожки',
            '573': 'Велотренажеры',
            '577': 'Эллиптические тренажеры',
            '581': 'Степперы и эскалаторы',
            '584': 'Гребные тренажеры',
            '592': 'Силовые тренажеры',
        }
        return result

    def _get_own_stock(self):
        url = 'https://sportpremier.ru/bitrix/catalog_export/yandex_all.php'
        response = requests.get(url, timeout=60)
        if response.status_code != 200:
            error = f'failed to download src xml file, response status: {response.status_code}, ' \
                    f'response text: {response.text}'
            _err(error)
            return error

        soup = BeautifulSoup(response.text, 'lxml')
        currencies = soup.find_all('currency')
        cats = soup.find_all('category')
        offers = soup.find_all('offer')
        _log('done')

    def get_suppliers_offers(self, category_ids):
        start = datetime.datetime.now()

        err = self._get_own_stock()
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
        error_count = 0

        for name, props in self._rows.items():

            has_price_diff = props.get('price') != props.get('own_price')
            props['has_price_diff'] = has_price_diff

            if has_price_diff:
                price_diff_count += 1

            if props.get('error'):
                error_count += 1

        return {
                   'duration': get_duration(start),
                   'supplier': self.supplier,
                   'supplier_url': self.supplier_base_url,
                   'rows': self._rows,
                   'price_diff_count': price_diff_count if price_diff_count > 0 else None,
                   'error_count': error_count if error_count > 0 else None,
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
                'category': self._cats.get(category_id),
                'category_url': category_url,
            }

            # name and url
            href_name = item.find('a')
            if href_name is not None:
                name = href_name.text
                props['good_name'] = name
                props['good_url'] = f'{self.supplier_base_url}{href_name.attrs.get("href")}'

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
                    _log('about to add name to props ...')
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
                props['url'] = f'{self_base_url}{name_href.attrs.get("href")}'
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

        with self._mutex:
            item_props = self._rows[name]
            for k, v in props.items():
                item_props[f'own_{k}'] = v
            self._rows[name] = item_props

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

        return stock_val, None

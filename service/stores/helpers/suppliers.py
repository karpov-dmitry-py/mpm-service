import requests
from bs4 import BeautifulSoup

from threading import Lock
from concurrent.futures import ThreadPoolExecutor

from .common import parse_int
from .common import _log

cyrillics = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'


def get_categories():
    result = {
        'Беговые дорожки': 569,
        'Велотренажеры': 573,
        'Эллиптические тренажеры': 577,
        'Степперы и эскалаторы': 581,
        'Гребные тренажеры': 584,
        'Силовые тренажеры': 592,
    }
    return result


def get_suppliers_offers_check_result(categories):
    base_url = 'https://neotren.ru'
    supplier = base_url.split('//')[1]
    # target_url = f'{base_url}/catalog?limit=1000000&category={",".join(categories)}'
    target_url = f'{base_url}/catalog?limit=10&category={",".join(categories)}'

    session = requests.Session()
    response = session.get(url=target_url, timeout=120)

    status = response.status_code
    if status != 200:
        return None, f'Ошибка при получении данных с сайта поставщика: {target_url}, код ответа: {status}, ' \
                     f'текст ответа: {response.text}'

    rows = dict()
    soup = BeautifulSoup(response.text, 'lxml')
    items = soup.find_all('table', class_='prodinfo')

    # parse supplier's site'
    for item in items:
        name = ''
        props = {
            'error': '',
        }

        # name and url
        href_name = item.find('a')
        if href_name is not None:
            name = href_name.text
            props['good_name'] = name
            props['good_url'] = f'{base_url}{href_name.attrs.get("href")}'

        # price
        price = item.find('span', class_='productPrice')
        if price is not None:
            price, err = parse_int(price.text)
            if price is not None:
                props['price'] = price

        # stock
        stock, err = _parse_stock(item)
        if stock is not None:
            props['stock'] = stock

        if name:
            rows[name] = props

    if not len(rows):
        return None, f'Не удалось распарсить сайт поставщика: {target_url}'

    mutex = Lock()
    with ThreadPoolExecutor(max_workers=min(len(rows), 50)) as executor:
        for name in rows:
            executor.submit(check_item, name=name, rows=rows, mutex=mutex)

    price_diff_count = 0
    error_count = 0

    for name, props in rows.items():
        has_price_diff = props.get('price') != props.get('own_price')
        props['has_price_diff'] = has_price_diff

        if has_price_diff:
            price_diff_count += 1

        if props.get('error'):
            error_count += 1

    return {
               'supplier': supplier,
               'supplier_url': base_url,
               'rows': rows,
               'price_diff_count': price_diff_count if price_diff_count > 0 else None,
               'error_count': error_count if error_count > 0 else None,
           }, None


def check_item(name, rows, mutex):
    """
    check item on own site
    """
    cleaned_name = ''.join([char for char in name.lower() if char not in cyrillics]).strip()
    if not cleaned_name:
        with mutex:
            rows[name]['error'] = f'Сформирована пустая строка поиска для товара "{name}"'
        return

    base_url = 'https://sportpremier.ru'
    target_url = f'{base_url}/search/?q={cleaned_name}'

    _log(f'searching own site for "{cleaned_name} ..."')
    response = requests.get(target_url, timeout=120)
    if response.status_code != 200:
        with mutex:
            rows[name]['error'] = f'Ошибка поиска товара "{cleaned_name}" на сайте {base_url}: ' \
                                  f'({response.status_code}) {response.text}'
        return

    soup = BeautifulSoup(response.text, 'lxml')
    items = soup.find_all('div', class_='item')
    if items is None or not len(items):
        with mutex:
            rows[name]['error'] = f'Пустой результат поиска товара "{cleaned_name}" на сайте {base_url}'
        return

    item = items[0]
    props = dict()

    name_div = item.find('div', class_='title')
    if name_div is not None:
        name_href = name_div.find('a')
        if name_href is not None:
            props['url'] = f'{base_url}{name_href.attrs.get("href")}'
            props['name'] = name_href.text
    if not len(props):
        with mutex:
            rows[name]['error'] = f'Не удалось распарсить наименование и ссылку на товар "{cleaned_name}" ' \
                                  f'на сайте {base_url}'
        return

    price_div = item.find('div', class_='price')
    if price_div is not None:
        price = price_div.text
        price_val, err = parse_int(price)
        if err:
            with mutex:
                rows[name]['error'] = f'Не удалось распарсить цену на товар "{cleaned_name}" ' \
                                      f'на сайте {base_url}'
            return

        props['price'] = price_val

    if props.get('price') is None:
        with mutex:
            rows[name]['error'] = f'Не удалось распарсить цену на товар "{cleaned_name}" ' \
                                  f'на сайте {base_url}'
        return

    with mutex:
        item_props = rows[name]
        for k, v in props.items():
            item_props[f'own_{k}'] = v
        rows[name] = item_props


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

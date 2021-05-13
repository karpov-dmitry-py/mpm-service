# from django.test import TestCase
# Create your tests here.

import requests


def test_update_stock():
    url = 'http://127.0.0.1:8000/api/v1/stock/'
    goods = [
        {
            'sku': '100500',
            'name': 'good 100500',
            'brand': 'TV',
            'stock': {
                'wh_01': 100,
                'wh_02': 200,
            }
        },
    ]
    _dict = {'offers': goods}
    response = requests.post(url, json=_dict)
    print(response.status_code)


if __name__ == '__main__':
    test_update_stock()

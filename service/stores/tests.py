# from django.test import TestCase
# Create your tests here.

import requests


def test_update_stock():
    url = 'http://127.0.0.1:8000/api/v1/stock/'
    headers = {
        'user-auth': 'admin@service.com',
        'token-auth': '569e68ac-8d66-44ce-8e54-ce91d0e6c3aa',
    }
    goods = [
        {
            'sku': '100500',
            'name': 'good 100500',
            'brand': 'TV',
            'stock': [
                {
                    'code': 'wh_code_01',
                    'available': 10,
                },
                {
                    'code': 'wh_code_02',
                    'available': 20,
                },
            ]
        },
    ]
    _dict = {'offers': goods}

    response = requests.post(url, headers=headers, json=_dict)
    print(response.status_code)


if __name__ == '__main__':
    test_update_stock()

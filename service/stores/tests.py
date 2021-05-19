# from django.test import TestCase
# Create your tests here.
import json

import requests


def test_update_stock():
    url = 'http://127.0.0.1:8000/api/v1/stock/'
    headers = {
        'user-auth': 'admin@service.com',
        'token-auth': '569e68ac-8d66-44ce-8e54-ce91d0e6c3aa',
    }
    # ''
    goods = [
        {
            'sku': '1001',
            'name': '1001 Тестовый товар, созданный  по апи',
            'brand': 'Banana Bros',
            'category': '3',
            'description': '1001 Тестовый товар по апи описание',
            'article': '1001_article',
            'barcode': 'test good 1001 barcode',
            'weight': 1.5,
            'pack_width': '20.4',
            'pack_height': '5.8',
            'pack_length': 10.5,
            'stocks': [
                {
                    'code': '56676476764334',
                    'available': 100,
                },
                {
                    'code': '4334234',
                    'available': 150,
                },
            ]
        },
        {
            'sku': 'cf2cc5dc-13c7-4791-ae49-45f5d30fe30b', # Товар # 1 (cf2cc5dc-1)
            'stocks': [
                {
                    'code': '56676476764334', # Ломоносовский пр, 100 (основной склад)
                    'available': 100,
                },
                {
                    'code': '3eq4523434234', # Новый склад 1 (без поставщика)
                    'available': 200,
                },
                {
                    'code': '76756667998',  # New 5
                    'available': 300,
                },
                {
                    'code': '090978976754ssd', # New 7
                    'available': 700,
                },
                # {
                #     'code': '76756667998', # New 5
                #     'available': '100ABC', # NOT AN INT
                # },
            ]
        },
    ]
    payload = []
    # payload = {'offers': goods}
    # with open('stock_request.json', 'w') as file:
    #     json.dump(payload, file, ensure_ascii=False, indent=4)

    response = requests.post(url, headers=headers, json=payload)
    try:
        print(response.json())

    except Exception as err:
        pass
    print(response.status_code)
    pass

if __name__ == '__main__':
    test_update_stock()

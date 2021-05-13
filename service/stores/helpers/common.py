import logging
import sys
import re

import uuid

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

EMAIL_RE = re.compile('^[\w.+\-]+@[\w]+\.[a-z]{2,3}$')
PHONE_PREFIX = '+7'


def _log(msg):
    logging.info(msg)


def _err(msg):
    logging.error(msg)


def _exc(exception):
    return f'error: ({exception.__class__.__name__}) {str(exception)}'


def is_valid_email(email):
    email = email or ''
    return bool(re.match(EMAIL_RE, email))


def strip_phone(phone):
    phone = phone or ''
    phone = phone.strip()
    return phone.replace(PHONE_PREFIX, '')


def format_phone(phone):
    phone = strip_phone(phone)
    if not phone:
        return
    return f'{PHONE_PREFIX}{phone}'


def get_valid_phone_length():
    return 10


def is_valid_phone(phone):
    phone = strip_phone(phone)
    return phone.isnumeric() and len(phone) == get_valid_phone_length()


def get_phone_error():
    return {'Неверно заполнен телефон': f'Необходимо ввести телефон из {get_valid_phone_length()} цифр'}


def get_email_error():
    return {'Неверно заполнен e-mail': f'Необходимо ввести корректный адрес электронной почты'}


def get_supplier_warehouse_type():
    return 'Склад поставщика'


def is_valid_supplier_choice(_type, supplier):
    if _type.name != get_supplier_warehouse_type():
        return True
    result = supplier is not None
    return result


def get_supplier_error():
    return {
        'Не заполнен поставщик': f'Необходимо указать поставщика для типа склада "{get_supplier_warehouse_type()}"'}

def new_uuid():
    return str(uuid.uuid4())

if __name__ == '__main__':
    email = 'sales@company.com'
    valid = is_valid_email(email)
    _log(valid)

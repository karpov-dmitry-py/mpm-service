import datetime
import logging
import sys
import os
import re
import time
import uuid
from contextlib import contextmanager

from django.http import FileResponse

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

EMAIL_RE = re.compile('^[\w.+\-]+@[\w]+\.[a-z]{2,3}$')
PHONE_PREFIX = '+7'
CONTENT_TYPES = {
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}


@contextmanager
def with_try(func):
    try:
        yield
    except (UnicodeDecodeError, UnicodeEncodeError, Exception) as err:
        err_msg = f'failed to {func}: {_exc(err)}'
        print(err_msg)
    finally:
        pass


@with_try('_log')
def _log(msg):
    logging.info(msg)


@with_try('_err')
def _err(msg):
    logging.error(msg)


def _exc(exception):
    return f'error: ({exception.__class__.__name__}) {str(exception)}'


def now_as_str():
    return datetime.datetime.now().strftime('%d%m%Y_%H%M%S')


def is_valid_email(_email):
    _email = _email or ''
    return bool(re.match(EMAIL_RE, _email))


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


def to_float(val):
    if val is None:
        return None
    if isinstance(val, float):
        return val
    if isinstance(val, str):
        patterns = (',',)
        for item in patterns:
            val = val.replace(item, '.')
    try:
        return float(val)
    except (TypeError, Exception) as err:
        err_msg = f'Failed to convert value {str(val)} to float: {_exc(err)}'
        _err(err_msg)
        return None


@contextmanager
def time_tracker(action):
    start = time.time()
    try:
        yield
    finally:
        end = time.time()
        duration = end - start
        _log(f'{action} took {duration} seconds.')


def get_duration(start):
    return str(datetime.datetime.now() - start)


def parse_int(src):
    src = str(src).lower().strip()
    sep = 'руб'
    src = src.split(sep)[0]

    if src.isnumeric():
        dst = src
    else:
        digits = [str(i) for i in range(10)]
        dst = ''.join([char for char in src if char in digits])
    try:
        result = int(dst)
        return result, None
    except (ValueError, Exception) as err:
        err_msg = f'failed to parse an int from {src}: {_exc(err)}'
        _err(err_msg)
        return None, err_msg


def get_file_response(src_path, target_filename, content_type, delete_after=False):
    try:
        content_type = CONTENT_TYPES.get(content_type, content_type)  # get full content type by a shorter simple alias
        response = FileResponse(
            open(src_path, 'rb'),
            as_attachment=True,
            content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename={target_filename}'
        if delete_after:
            os.remove(src_path)
        return response, None
    except (OSError, Exception) as err:
        err_msg = f'Не удалось сформировать ответ по файлу {src_path}: {_exc(err)}'
        _err(err_msg)
        return None, err_msg


if __name__ == '__main__':
    email = 'sales@company.com'
    valid = is_valid_email(email)
    _log(valid)

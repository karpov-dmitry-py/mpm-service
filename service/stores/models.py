from datetime import datetime

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import CASCADE
from django.db.models import SET_NULL
from django.utils import timezone

from .helpers.common import new_uuid

ACTIVE_STORE_STATUS = 'подключен'


def now():
    if settings.USE_TZ:
        tz = timezone.get_default_timezone()
        _now = datetime.now(tz=tz)
        return _now
    else:
        return datetime.now()


class StoreStatus(models.Model):
    name = models.CharField(verbose_name='Название', max_length=100)
    description = models.TextField(verbose_name='Описание', max_length=500, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'store_statuses'
        verbose_name = 'Статус магазина'
        verbose_name_plural = 'Статусы магазина'


class StoreType(models.Model):
    name = models.CharField(verbose_name='Название', max_length=100)
    description = models.TextField(verbose_name='Описание', max_length=500, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'store_types'
        verbose_name = 'Тип магазина'
        verbose_name_plural = 'Типы магазина'


class Marketplace(models.Model):
    name = models.CharField(verbose_name='Название', max_length=100)
    api_url = models.CharField(verbose_name='API URL', max_length=500)
    code = models.CharField(verbose_name='Код', max_length=200, blank=True, null=True)
    description = models.TextField(verbose_name='Описание', max_length=500, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'marketplaces'
        verbose_name = 'Маркетплейс'
        verbose_name_plural = 'Маркетплейсы'


class Store(models.Model):
    name = models.CharField(verbose_name='Название', max_length=200)
    description = models.TextField(verbose_name='Описание', max_length=500, null=True, blank=True)
    store_type = models.ForeignKey(StoreType, on_delete=CASCADE, verbose_name='Тип')
    marketplace = models.ForeignKey(Marketplace, on_delete=CASCADE, verbose_name='Маркетплейс')
    status = models.ForeignKey(StoreStatus, on_delete=CASCADE, verbose_name='Статус')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Аккаунт')

    def __str__(self):
        # noinspection PyUnresolvedReferences
        return f'{self.marketplace} -> {self.name}'

    # noinspection PyUnresolvedReferences
    def get_prop(self, prop_name):
        rows = StoreProperty.objects.filter(store=self).filter(property__name=prop_name)
        if not rows:
            return
        return rows[0].value

    def is_active(self):
        return self.status.name.lower() == ACTIVE_STORE_STATUS

    class Meta:
        db_table = 'stores'
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'


class MarketplaceProperty(models.Model):
    marketplace = models.ForeignKey(Marketplace, on_delete=CASCADE, verbose_name='Маркетплейс')
    name = models.CharField(verbose_name='Название', max_length=200)
    description = models.TextField(verbose_name='Описание', max_length=500, null=True, blank=True)
    mandatory = models.BooleanField(default=True, verbose_name='Обязательно для создания магазина')

    def __str__(self):
        return f'{self.marketplace} -> {self.name}{" (обяз.)" if self.mandatory else ""}'

    class Meta:
        db_table = 'marketplaces_api_properties'
        verbose_name = 'Свойство маркетплейса'
        verbose_name_plural = 'Свойства маркетплейса'


class StoreProperty(models.Model):
    store = models.ForeignKey(Store, on_delete=CASCADE, verbose_name='Магазин')
    property = models.ForeignKey(MarketplaceProperty, on_delete=CASCADE, verbose_name='Свойство')
    value = models.CharField(verbose_name='Значение', max_length=1000)

    def __str__(self):
        # noinspection PyUnresolvedReferences
        return f'({self.store.name} - {self.store.marketplace}) {self.property.name}: {self.value}'

    class Meta:
        db_table = 'stores_api_properties'
        verbose_name = 'Значение свойства магазина'
        verbose_name_plural = 'Значения свойств магазина'


class GoodsBrand(models.Model):
    name = models.CharField(verbose_name='Название', max_length=500)
    description = models.TextField(verbose_name='Описание', max_length=500, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Аккаунт')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'goods_brands'
        verbose_name = 'Бренд товара'
        verbose_name_plural = 'Бренды товаров'
        ordering = ['id']


class GoodsCategory(models.Model):
    name = models.CharField(verbose_name='Название', max_length=500)
    description = models.TextField(verbose_name='Описание', max_length=500, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               verbose_name='Родительская категория')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Аккаунт')

    def __str__(self):
        return self.name if not self.parent else f'{self.parent} \\ {self.name}'

    class Meta:
        db_table = 'goods_categories'
        verbose_name = 'Категория товара'
        verbose_name_plural = 'Категории товаров'
        ordering = ['id']


class Good(models.Model):
    sku = models.CharField(verbose_name='Код', max_length=100)
    article = models.CharField(verbose_name='Артикул', max_length=100, null=True, blank=True)
    name = models.CharField(verbose_name='Наименование', max_length=1000)
    description = models.TextField(verbose_name='Описание', max_length=1000, null=True, blank=True)
    brand = models.ForeignKey(GoodsBrand, on_delete=SET_NULL, null=True, blank=True, verbose_name='Бренд')
    category = models.ForeignKey(GoodsCategory, on_delete=SET_NULL, null=True, blank=True,
                                 verbose_name='Категория')
    weight = models.FloatField(verbose_name='Вес, кг', null=True, blank=True)
    pack_width = models.FloatField(verbose_name='Ширина упаковки, см', null=True, blank=True)
    pack_length = models.FloatField(verbose_name='Длина упаковки, см', null=True, blank=True)
    pack_height = models.FloatField(verbose_name='Высота упаковки, см', null=True, blank=True)
    barcode = models.CharField(verbose_name='Штрихкод', max_length=100, null=True, blank=True)
    date_created = models.DateTimeField(verbose_name='Дата создания', blank=True)
    date_updated = models.DateTimeField(verbose_name='Дата изменения', blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, verbose_name='Аккаунт')

    def __str__(self):
        result = f'(sku: {self.sku}) {self.name} {self.brand if self.brand else ""} ' \
                 f'{self.article if self.article else ""}'
        return result

    def save(self, *args, **kwargs):
        _now = now()
        if not self.pk:
            self.date_created = _now
        self.date_updated = _now
        return super().save(*args, **kwargs)

    class Meta:
        db_table = 'goods'
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        unique_together = ('sku', 'user')
        ordering = ['id']


class WarehouseType(models.Model):
    name = models.CharField(verbose_name='Название', max_length=100)
    description = models.TextField(verbose_name='Описание', max_length=500, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'warehouse_types'
        verbose_name = 'Тип склада'
        verbose_name_plural = 'Типы склада'


class Supplier(models.Model):
    name = models.CharField(verbose_name='Наименование', max_length=1000)
    tin = models.CharField(verbose_name='ИНН', max_length=30, blank=True, null=True)
    contact = models.CharField(verbose_name='Контактное лицо', max_length=200, blank=True, null=True)
    email = models.CharField(verbose_name='E-mail', max_length=200, blank=True, null=True)
    phone = models.CharField(verbose_name='Телефон', max_length=12, blank=True, null=True)
    description = models.TextField(verbose_name='Описание', max_length=1000, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Аккаунт')

    def __str__(self):
        # noinspection PyUnresolvedReferences
        return f'{self.name}'

    def get_warehouses(self):
        items = getattr(self, 'warehouses')
        if not items:
            return []
        result = []
        for item in items.all():
            _dict = {
                'id': item.id,
                'name': item.name,
            }
            result.append(_dict)
        return result

    class Meta:
        db_table = 'suppliers'
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'


class Warehouse(models.Model):
    name = models.CharField(verbose_name='Наименование', max_length=1000)
    active = models.BooleanField(verbose_name='Активность', default=True, blank=True)
    kind = models.ForeignKey(WarehouseType, on_delete=CASCADE, verbose_name='Тип склада')
    supplier = models.ForeignKey(Supplier, on_delete=CASCADE, verbose_name='Поставщик', related_name='warehouses',
                                 blank=True, null=True)
    code = models.CharField(verbose_name='Символьный код', max_length=200, blank=False, null=False)
    priority = models.IntegerField(verbose_name='Приоритет', blank=True, null=True)
    description = models.TextField(verbose_name='Описание', max_length=1000, null=True, blank=True)
    stores = models.ManyToManyField(Store, verbose_name='Магазин', related_name='warehouses', blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Аккаунт')

    def __str__(self):
        # noinspection PyUnresolvedReferences
        return f'({self.user.email}) {self.name}'

    def get_stores(self):
        result = []
        # noinspection PyUnresolvedReferences
        for item in self.stores.all():
            _dict = {
                'id': item.id,
                'name': item.name,
            }
            result.append(_dict)
        return result

    class Meta:
        db_table = 'warehouses'
        verbose_name = 'Склад'
        verbose_name_plural = 'Склады'


class Stock(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=CASCADE, verbose_name='Склад', related_name='stock',
                                  blank=False, null=False)
    good = models.ForeignKey(Good, on_delete=CASCADE, verbose_name='Товар', related_name='stock',
                             blank=False, null=False)
    amount = models.PositiveIntegerField(verbose_name='Количество', blank=False, null=False)
    date_updated = models.DateTimeField(verbose_name='Дата изменения', blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, verbose_name='Аккаунт')

    def __str__(self):
        return f'({self.warehouse.name})/{self.good.name}: {self.amount}'

    def save(self, *args, **kwargs):
        self.date_updated = now()
        return super().save(*args, **kwargs)

    class Meta:
        db_table = 'stock'
        verbose_name = 'Запись об остатке товара'
        verbose_name_plural = 'Остатки товаров'
        ordering = ['id']


class System(models.Model):
    name = models.CharField(verbose_name='Наименование', max_length=1000)
    code = models.CharField(verbose_name='Код', max_length=200, blank=False)
    token = models.CharField(verbose_name='Токен', max_length=36, blank=True)
    description = models.TextField(verbose_name='Описание', max_length=1000, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, verbose_name='Аккаунт')

    def __str__(self):
        return f'({self.code}) {self.name}'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.token = new_uuid()
        return super().save(*args, **kwargs)

    class Meta:
        db_table = 'systems'
        verbose_name = 'Учетная система'
        verbose_name_plural = 'Учетные системы'
        ordering = ['id']


class StoreWarehouse(models.Model):
    name = models.CharField(verbose_name='Наименование', max_length=500, blank=False, null=False)
    code = models.CharField(verbose_name='Код в маркетплейсе', max_length=100, blank=False, null=False)
    description = models.TextField(verbose_name='Описание', blank=True, null=True)
    store = models.ForeignKey(Store, verbose_name='Магазин', on_delete=CASCADE, related_name='store_warehouses',
                              related_query_name='warehouse', blank=True, null=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, verbose_name='Аккаунт')

    def __str__(self):
        return f'({self.store.name}) {self.name}'

    # noinspection PyUnresolvedReferences
    def stock_update_available(self):
        marketplaces = ('ozon',)
        return self.store.marketplace.name.lower().strip() in marketplaces

    class Meta:
        db_table = 'store_warehouses'
        verbose_name = 'Склад магазина'
        verbose_name_plural = 'Склады магазинов'
        ordering = ['id']


class StockSetting(models.Model):
    name = models.CharField(verbose_name='Наименование', max_length=500, blank=False, null=False)
    priority = models.PositiveIntegerField(verbose_name='Порядок', blank=False, null=False,
                                           validators=[MinValueValidator(1), ])
    content = models.TextField(verbose_name='Условия', blank=True, null=False)
    description = models.TextField(verbose_name='Описание', max_length=1000, null=True, blank=True)
    warehouse = models.ForeignKey(StoreWarehouse, verbose_name='Склад магазина', on_delete=CASCADE,
                                  related_name='stock_settings', blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, verbose_name='Аккаунт')

    def __str__(self):
        if self.warehouse:
            return f'({self.warehouse.name}) {self.name}'
        else:
            return self.name

    class Meta:
        db_table = 'stock_settings'
        verbose_name = 'Настройка остатков товаров'
        verbose_name_plural = 'Настройки остатков товаров'
        ordering = ['priority']


class Log(models.Model):
    end_date = models.DateTimeField(verbose_name='Дата выполнения', blank=True)
    marketplace = models.ForeignKey(Marketplace, verbose_name='Маркетплейс', on_delete=CASCADE,
                                    related_name='logs', blank=True, null=True)
    store = models.ForeignKey(Store, verbose_name='Магазин', on_delete=CASCADE,
                              related_name='logs', blank=True, null=True)
    warehouse = models.ForeignKey(StoreWarehouse, verbose_name='Склад магазина', on_delete=CASCADE,
                                  related_name='logs', blank=True, null=True)
    success = models.BooleanField(default=True, verbose_name='Успех', blank=True)
    duration = models.FloatField(verbose_name='Длительность, сек.', null=True, blank=True)
    request = models.TextField(verbose_name='Запрос', null=True, blank=True)
    response = models.TextField(verbose_name='Ответ', null=True, blank=True)
    response_status = models.IntegerField(default=200, verbose_name='HTTP-код ответа', blank=True)
    error = models.CharField(verbose_name='Описание ошибки', max_length=5000, null=True, blank=True)
    comment = models.TextField(verbose_name='Комментарий', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, verbose_name='Аккаунт', blank=True, null=True)

    def __str__(self):
        date_format = '%Y-%m-%dT%H:%M:%S %Z'
        return f'({self.end_date.strftime(date_format)}) склад магазина: ' \
               f'{self.warehouse.name if self.warehouse else ""}, ' \
               f'{"успешно" if self.success else "ошибка"}, код ответа: {self.response_status}'

    def save(self, *args, **kwargs):
        self.end_date = now()
        return super().save(*args, **kwargs)

    class Meta:
        db_table = 'logs'
        verbose_name = 'Лог обмена'
        verbose_name_plural = 'Логи обмена'
        ordering = ['-end_date']


class LogRow(models.Model):
    log = models.ForeignKey(Log, verbose_name='Лог обмена', on_delete=CASCADE, related_name='rows')
    good = models.ForeignKey(Good, verbose_name='Товар', on_delete=CASCADE, related_name='logs', blank=True, null=True)
    sku = models.CharField(verbose_name='SKU товара', max_length=100, blank=True, null=True)
    amount = models.PositiveIntegerField(verbose_name='Переданный остаток', default=0, blank=True)
    success = models.BooleanField(default=True, verbose_name='Успешно', blank=True)
    err_code = models.CharField(verbose_name='Код ошибки', max_length=100, blank=True, null=True)
    err_msg = models.CharField(verbose_name='Текст ошибки', max_length=200, blank=True, null=True)

    # noinspection PyUnresolvedReferences
    def __str__(self):
        return f'(лог {self.log.id}) ({self.good.sku if self.good else self.sku})' \
               f' {self.good.name if self.good else "нет карточки товара"} - {self.amount} ' \
               f'- {"успешно" if self.success else "ошибка"}'

    class Meta:
        db_table = 'log_rows'
        verbose_name = 'Строка лога обмена'
        verbose_name_plural = 'Строки логов обмена'
        ordering = ['id']


class Job(models.Model):
    name = models.CharField(verbose_name='Наименование', max_length=500, blank=False, null=False)
    code = models.CharField(verbose_name='Уникальный код', max_length=100, blank=False, null=False, unique=True)
    description = models.TextField(verbose_name='Описание', blank=True, null=True)

    def __str__(self):
        return f'{self.name} (код: {self.code})'

    class Meta:
        db_table = 'jobs'
        verbose_name = 'Задача по расписанию'
        verbose_name_plural = 'Список задач по расписанию'
        ordering = ['id']


class JobState(models.Model):
    name = models.CharField(verbose_name='Наименование', max_length=500, blank=False, null=False)
    code = models.CharField(verbose_name='Уникальный код', max_length=100, blank=False, null=False, unique=True)
    description = models.TextField(verbose_name='Описание', blank=True, null=True)

    def __str__(self):
        return f'{self.name} (код: {self.code})'

    class Meta:
        db_table = 'job_states'
        verbose_name = 'Состояние задачи'
        verbose_name_plural = 'Состояния задач'
        ordering = ['id']


class UserJob(models.Model):
    name = models.CharField(verbose_name='Наименование', max_length=500, blank=False, null=False)
    active = models.BooleanField(default=True, verbose_name='Задача активна', blank=True)
    schedule = models.CharField(verbose_name='Расписание', max_length=500, blank=True, null=False)
    description = models.TextField(verbose_name='Описание', blank=True, null=True)
    job = models.ForeignKey(Job, verbose_name='Задача по расписанию', on_delete=CASCADE,
                            related_name='user_jobs', blank=False, null=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, verbose_name='Аккаунт', related_name='jobs')

    def __str__(self):
        return f'({self.user}) {self.name} ({"активная" if self.active else "не активная"})'

    class Meta:
        db_table = 'user_jobs'
        verbose_name = 'Периодическая задача пользователя'
        verbose_name_plural = 'Периодические задачи пользователей'
        unique_together = [['job', 'user']]
        ordering = ['id']


class UserJobLog(models.Model):
    start_date = models.DateTimeField(verbose_name='Дата начала', blank=True)
    end_date = models.DateTimeField(verbose_name='Дата завершения', blank=True)
    duration = models.DurationField(verbose_name='Длительность', null=True, blank=True)
    success = models.BooleanField(default=True, verbose_name='Успешно', blank=True)
    error = models.CharField(verbose_name='Ошибка', max_length=5000, blank=True, null=True)
    state = models.ForeignKey(JobState, verbose_name='Состояние', on_delete=CASCADE, related_name='user_job_logs')
    job = models.ForeignKey(UserJob, verbose_name='Задача', on_delete=CASCADE, related_name='logs')

    # noinspection PyUnresolvedReferences
    def __str__(self):
        return f'({self.job.user.username}) {self.job.name}, {self.state.name}'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.start_date = now()
        return super().save(*args, **kwargs)

    class Meta:
        db_table = 'user_job_logs'
        verbose_name = 'Лог периодической задачи пользователя'
        verbose_name_plural = 'Логи периодических задач пользователей'
        ordering = ['-start_date']


class OrderStatus(models.Model):
    name = models.CharField(verbose_name='Наименование', max_length=200)
    code = models.CharField(verbose_name='Код', max_length=200, blank=False)
    description = models.TextField(verbose_name='Описание', null=True, blank=True)

    def __str__(self):
        return f'({self.code}) {self.name}'

    class Meta:
        db_table = 'order_statuses'
        verbose_name = 'Статус заказа покупателя'
        verbose_name_plural = 'Статусы заказов покупателей'
        ordering = ['id']


class OrderMarketplaceStatus(models.Model):
    name = models.CharField(verbose_name='Наименование', max_length=200)
    code = models.CharField(verbose_name='Код', max_length=200, blank=False)
    marketplace = models.ForeignKey(Marketplace, verbose_name='Маркетплейс', on_delete=CASCADE, related_name='statuses')
    status = models.ForeignKey(OrderStatus, verbose_name='Системный статус', on_delete=CASCADE,
                               related_name='marketplace_statuses')
    description = models.TextField(verbose_name='Описание', null=True, blank=True)

    def __str__(self):
        return f'({self.marketplace} - {self.code}) {self.name}'

    class Meta:
        db_table = 'order_marketplace_statuses'
        verbose_name = 'Статус заказа покупателя в маркетплейсе'
        verbose_name_plural = 'Статусы заказов покупателей в маркетплейсах'
        ordering = ['id']


class Order(models.Model):
    created_at = models.DateTimeField(verbose_name='Дата создания', blank=True)
    updated_at = models.DateTimeField(verbose_name='Дата изменения', blank=True, null=True)
    marketplace = models.ForeignKey(Marketplace, verbose_name='Маркетплейс', on_delete=CASCADE, related_name='orders')
    order_marketplace_id = models.CharField(verbose_name='Номер заказа в маркетплейсе', max_length=100, blank=True)
    order_acc_system_id = models.CharField(verbose_name='Номер заказа в учетной системе', max_length=100, blank=True,
                                           null=True)
    status = models.ForeignKey(OrderStatus, verbose_name='Статус', on_delete=CASCADE, related_name='orders', blank=True,
                               null=True)
    store = models.ForeignKey(Store, verbose_name='Магазин', on_delete=CASCADE, related_name='orders')
    store_warehouse = models.ForeignKey(StoreWarehouse, verbose_name='Склад магазина', on_delete=CASCADE,
                                        related_name='orders', blank=True, null=True)
    region = models.CharField(verbose_name='Регион', max_length=100, blank=True, null=True)
    items_total = models.FloatField(verbose_name='Сумма товаров', blank=True, null=True)
    subsidy_total = models.FloatField(verbose_name='Сумма компенсации от маркетплейса', blank=True, null=True)
    total = models.FloatField(verbose_name='Общая сумма', blank=True, null=True)
    comment = models.TextField(verbose_name='Комментарий', blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, verbose_name='Аккаунт', related_name='orders')

    def __str__(self):
        return f'(id: {self.pk}, {self.marketplace}/{self.order_marketplace_id}) ' \
               f'{self.created_at} {self.total}'

    def save(self, *args, **kwargs):
        _now = now()

        if not self.pk:
            self.date_created = _now
        if self.pk:
            self.date_updated = _now

        return super().save(*args, **kwargs)

    class Meta:
        db_table = 'orders'
        verbose_name = 'Заказ покупателя'
        verbose_name_plural = 'Заказы покупателей'
        ordering = ['id']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Заказ', on_delete=CASCADE, related_name='items')
    good = models.ForeignKey(Good, verbose_name='Товар', on_delete=CASCADE, related_name='order_items')
    count = models.IntegerField(verbose_name='Количество', blank=True)
    price = models.FloatField(verbose_name='Цена', blank=True)

    # noinspection PyUnresolvedReferences
    def __str__(self):
        return f'(Заказ {self.order.id}) {self.good.sku} {self.good.name} {self.count} *  {self.price}'

    class Meta:
        db_table = 'order_items'
        verbose_name = 'Строка заказа покупателя'
        verbose_name_plural = 'Строки заказов покупателей'
        ordering = ['id']


class OrderShipment(models.Model):
    order = models.ForeignKey(Order, verbose_name='Заказ', on_delete=CASCADE, related_name='shipments')
    shipment_id = models.CharField(verbose_name='Идентификатор грузового места', max_length=100, blank=True, null=True)
    shipment_date = models.DateTimeField(verbose_name='Требуемая дата отгрузки места в доставку', blank=True, null=True)

    # noinspection PyUnresolvedReferences
    def __str__(self):
        return f'(Заказ {self.order.id}) {self.shipment_id} {self.shipment_date}'

    class Meta:
        db_table = 'order_shipments'
        verbose_name = 'Грузовые места заказа покупателя'
        verbose_name_plural = 'Грузовые места заказов покупателя'
        ordering = ['shipment_id']

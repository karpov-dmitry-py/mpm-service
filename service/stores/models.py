from datetime import datetime

from django.conf import settings
from django.db import models
from django.db.models import CASCADE
from django.db.models import SET_NULL
from django.utils import timezone

from .helpers.common import new_uuid


def _now():
    if settings.USE_TZ:
        tz = timezone.get_default_timezone()
        now = datetime.now(tz=tz)
        return now
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
        now = _now()
        if not self.pk:
            self.date_created = now
        self.date_updated = now
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
    code = models.CharField(verbose_name='Символьный код', max_length=200, blank=True, null=True)
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
        self.date_updated = _now()
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

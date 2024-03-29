# Generated by Django 3.1.7 on 2021-04-15 20:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stores', '0006_good_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1000, verbose_name='Наименование')),
                ('tin', models.CharField(blank=True, max_length=30, null=True, verbose_name='ИНН')),
                ('contact', models.CharField(blank=True, max_length=200, null=True, verbose_name='Контактное лицо')),
                ('email', models.CharField(blank=True, max_length=200, null=True, verbose_name='E-mail')),
                ('phone', models.CharField(blank=True, max_length=12, null=True, verbose_name='Телефон')),
                ('description', models.TextField(blank=True, max_length=1000, null=True, verbose_name='Описание')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Аккаунт')),
            ],
            options={
                'verbose_name': 'Поставщик',
                'verbose_name_plural': 'Поставщики',
                'db_table': 'suppliers',
            },
        ),
        migrations.CreateModel(
            name='WarehouseType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название')),
                ('description', models.TextField(blank=True, max_length=500, null=True, verbose_name='Описание')),
            ],
            options={
                'verbose_name': 'Тип склада',
                'verbose_name_plural': 'Типы складов',
                'db_table': 'warehouse_types',
            },
        ),
        migrations.CreateModel(
            name='Warehouse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1000, verbose_name='Наименование')),
                ('active', models.BooleanField(blank=True, default=True, verbose_name='Активность')),
                ('code', models.CharField(blank=True, max_length=200, null=True, verbose_name='Символьный код')),
                ('priority', models.IntegerField(blank=True, null=True, verbose_name='Приоритет')),
                ('description', models.TextField(blank=True, max_length=1000, null=True, verbose_name='Описание')),
                ('kind', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stores.warehousetype', verbose_name='Тип склада')),
                ('stores', models.ManyToManyField(blank=True, related_name='warehouses', to='stores.Store', verbose_name='Магазин')),
                ('supplier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='warehouses', to='stores.supplier', verbose_name='Поставщик')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Аккаунт')),
            ],
            options={
                'verbose_name': 'Склад',
                'verbose_name_plural': 'Склады',
                'db_table': 'warehouses',
            },
        ),
    ]

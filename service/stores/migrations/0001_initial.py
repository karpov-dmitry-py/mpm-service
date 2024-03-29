# Generated by Django 3.1.7 on 2021-03-07 13:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Marketplace',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название')),
                ('api_url', models.CharField(max_length=500, verbose_name='API URL')),
                ('description', models.TextField(blank=True, max_length=500, null=True, verbose_name='Описание')),
            ],
            options={
                'verbose_name': 'Маркетплейс',
                'verbose_name_plural': 'Маркетплейсы',
                'db_table': 'marketplaces',
            },
        ),
        migrations.CreateModel(
            name='StoreStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название')),
                ('description', models.TextField(blank=True, max_length=500, null=True, verbose_name='Описание')),
            ],
            options={
                'verbose_name': 'Статус магазина',
                'verbose_name_plural': 'Статусы магазина',
                'db_table': 'store_statuses',
            },
        ),
        migrations.CreateModel(
            name='StoreType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название')),
                ('description', models.TextField(blank=True, max_length=500, null=True, verbose_name='Описание')),
            ],
            options={
                'verbose_name': 'Тип магазина',
                'verbose_name_plural': 'Типы магазина',
                'db_table': 'store_types',
            },
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название')),
                ('description', models.TextField(blank=True, max_length=500, null=True, verbose_name='Описание')),
                ('_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stores.storetype', verbose_name='Тип')),
                ('marketplace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stores.marketplace', verbose_name='Маркетплейс')),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stores.storestatus', verbose_name='Статус')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Аккаунт')),
            ],
            options={
                'verbose_name': 'Магазин',
                'verbose_name_plural': 'Магазины',
                'db_table': 'stores',
            },
        ),
    ]

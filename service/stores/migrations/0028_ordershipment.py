# Generated by Django 3.1.7 on 2022-03-07 17:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0027_auto_20220307_1952'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderShipment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shipment_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='Идентификатор грузового места')),
                ('shipment_date', models.DateTimeField(blank=True, null=True, verbose_name='Требуемая дата отгрузки места в доставку')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shipments', to='stores.order', verbose_name='Заказ')),
            ],
            options={
                'verbose_name': 'Грузовые места заказа покупателя',
                'verbose_name_plural': 'Грузовые места заказов покупателя',
                'db_table': 'order_shipments',
                'ordering': ['shipment_id'],
            },
        ),
    ]
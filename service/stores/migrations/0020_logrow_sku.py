# Generated by Django 3.1.7 on 2021-11-04 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0019_auto_20211003_1704'),
    ]

    operations = [
        migrations.AddField(
            model_name='logrow',
            name='sku',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='SKU товара'),
        ),
    ]

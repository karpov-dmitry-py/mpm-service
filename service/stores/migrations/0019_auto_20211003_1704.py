# Generated by Django 3.1.7 on 2021-10-03 14:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0018_logrow'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logrow',
            name='good',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='stores.good', verbose_name='Товар'),
        ),
    ]

# Generated by Django 3.1.7 on 2021-11-16 21:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0024_auto_20211116_1137'),
    ]

    operations = [
        migrations.AddField(
            model_name='userjoblog',
            name='duration',
            field=models.DurationField(blank=True, null=True, verbose_name='Длительность'),
        ),
    ]

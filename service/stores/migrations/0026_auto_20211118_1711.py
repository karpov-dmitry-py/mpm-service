# Generated by Django 3.1.7 on 2021-11-18 14:11

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stores', '0025_userjoblog_duration'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='userjob',
            unique_together={('job', 'user')},
        ),
    ]

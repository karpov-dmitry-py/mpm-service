import time

from django.db.models.signals import post_save
from django.db.models.signals import post_delete

from .models import UserJob

from .helpers.scheduler import Scheduler
from .helpers.common import new_uuid


def update_cron_job(sender, instance, **kwargs):
    username = instance.user.username
    if not instance.active:
        Scheduler().drop_job(username)
        return
    Scheduler().update_job(username, instance.schedule)


def drop_cron_job(sender, instance, **kwargs):
    Scheduler().drop_job(instance.user.username)


# cron job
post_save.connect(update_cron_job, sender=UserJob, dispatch_uid=new_uuid())
post_delete.connect(drop_cron_job, sender=UserJob, dispatch_uid=new_uuid())

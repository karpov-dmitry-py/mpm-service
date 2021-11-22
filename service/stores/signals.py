from django.db.models.signals import post_save
from django.db.models.signals import post_delete
# from django.dispatch import receiver
from .models import UserJob

from .helpers.scheduler import Scheduler
from .helpers.common import new_uuid


# noinspection PyUnusedLocal
# @receiver(post_save, sender=UserJob)
def update_cron_job(sender, instance, **kwargs):
    username = instance.user.username
    if not instance.active:
        Scheduler().drop_job(username)
        return
    Scheduler().update_job(username, instance.schedule)


# noinspection PyUnusedLocal
# @receiver(post_delete, sender=UserJob)
def drop_cron_job(sender, instance, **kwargs):
    Scheduler().drop_job(instance.user.username)


post_save.connect(update_cron_job, sender=UserJob, dispatch_uid=new_uuid())
post_delete.connect(drop_cron_job, sender=UserJob, dispatch_uid=new_uuid())

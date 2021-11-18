from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserJob

# noinspection PyProtectedMember
from .helpers.common import _log


# noinspection PyUnusedLocal
@receiver(post_save, sender=UserJob)
def create_profile(sender, instance, created, **kwargs):
    if created:
        _log('a user job has been created')


# noinspection PyUnusedLocal
@receiver(post_save, sender=UserJob)
def save_profile(sender, instance, **kwargs):
    _log('a user job has been updated')


from django.apps import AppConfig
# from .helpers.scheduler import Worker


class StoresConfig(AppConfig):
    name = 'stores'

    def ready(self):
        # Worker().start_jobs()
        pass

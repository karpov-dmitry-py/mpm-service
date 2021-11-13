from django.apps import AppConfig

class StoresConfig(AppConfig):
    name = 'stores'

    def ready(self):
        pass
        # scheduler.Worker().start_jobs()


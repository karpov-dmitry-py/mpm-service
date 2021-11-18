from django.apps import AppConfig


class StoresConfig(AppConfig):
    name = 'stores'

    # noinspection PyUnresolvedReferences
    def ready(self):
        import stores.signals

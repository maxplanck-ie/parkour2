from django.apps import AppConfig


class PoolingConfig(AppConfig):
    name = 'pooling'

    def ready(self):
        import pooling.signals

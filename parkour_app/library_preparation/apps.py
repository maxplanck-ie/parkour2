from django.apps import AppConfig


class LibraryPreparationConfig(AppConfig):
    name = 'library_preparation'
    verbose_name = 'Library Preparation'

    def ready(self):
        import library_preparation.signals

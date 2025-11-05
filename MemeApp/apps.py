from django.apps import AppConfig

class MemeappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'MemeApp'
    verbose_name = 'Меми'

    def ready(self):
        # Імпортуємо для активації сигналів
        from . import models
from django.apps import AppConfig
import threading
#
# def bot_on():
#     import tg_bot


class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base'

    # def ready(self):
    #     print('я дэбил')
    #     t = threading.Thread(target=bot_on)
    #     a = False
    #     t.start()

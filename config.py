import os

HEADLESS = True
DEBUG = os.environ.get('DEBUG', False)

# proxy
# REQUEST_KWARGS = {"proxy_url": "socks5://localhost:9050/"}
REQUEST_KWARGS = {}

# secrets
if DEBUG:
    from secrets_local import ADMIN_KEY, MONGO_SETTINGS, YANDEX_LOGIN, YANDEX_PASSWORD, TOKEN
else:
    ADMIN_KEY = os.environ['ADMIN_KEY']
    YANDEX_LOGIN = os.environ['YANDEX_LOGIN']
    YANDEX_PASSWORD = os.environ['YANDEX_PASSWORD']
    TOKEN = os.environ['TOKEN']  # telegram token

    # db config
    MONGO_SETTINGS = {
        "DB_NAME": "taxi",
        "HOST": "localhost",
        "PORT": 27017,
        "USERNAME": os.environ['DB_USERNAME'],
        "PASSWORD": os.environ['DB_PASSWORD'],
    }

PENALTIES = {
    0: {
        "type": "warning",
        "message": "Внимание! Вы не на линии!"
    },
    1: {
        "type": "warning",
        "message":
        "Внимание! Вы не на линии! Отправьте голосовое сообщение с объяснением.",
        "button": "send_testify",
    },
    2: {
        "type": "warning",
        "message":
        "Внимание! Вы не на линии! Отправьте голосовое сообщение с объяснением.",
        "button": "send_testify",
    },
    3: {
        "type":
        "call_dispatcher",
        "message":
        "ВНИМАНИЕ! "
        "Водитель: {name} {surname}, находился в статусе 'ЗАНЯТ' длительное время "
        "Объяснительная не получена! Телефон водителя: {phone} Телеграм: {tg_name}",
        "update_timeout":
        30,  # minutes
    },
}

try:
    from config_local import *
except ImportError:
    pass

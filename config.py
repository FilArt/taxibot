HEADLESS = True
DEBUG = False

# proxy
REQUEST_KWARGS = {"proxy_url": "socks5://localhost:9050/"}

# secrets
TEST_CHAT_ID = ""
ADMIN_KEY = ""
YANDEX_LOGIN = ""
YANDEX_PASSWORD = ""
TOKEN = ""  # telegram token

# db config
MONGO_SETTINGS = {
    "DB_NAME": "taxi",
    "HOST": "localhost",
    "PORT": 27017,
    "USERNAME": "",
    "PASSWORD": "",
}

PENALTIES = {
    0: {"type": "warning", "message": "Внимание! Вы не на линии!"},
    1: {
        "type": "warning",
        "message": "Внимание! Вы не на линии! Отправьте голосовое сообщение с объяснением.",
        "button": "send_testify",
    },
    2: {
        "type": "warning",
        "message": "Внимание! Вы не на линии! Отправьте голосовое сообщение с объяснением.",
        "button": "send_testify",
    },
    3: {
        "type": "call_dispatcher",
        "message": "ВНИМАНИЕ! Свяжитесь с водителем. "
        "Водитель: {name} {surname}, находился в статусе 'ЗАНЯТ' более 20 минут!!! "
        "Объяснительная не получена! Телефон водителя: {phone} Телеграм: {tg_name}",
        "update_timeout": 2 * 60,
    },
}

try:
    from config_local import *
except ImportError:
    pass

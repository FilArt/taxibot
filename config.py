import time

HEADLESS = True
DEBUG = False

# proxy
REQUEST_KWARGS = {
    'proxy_url': 'socks5://localhost:9050/',
}

# secrets
TEST_CHAT_ID = ''
ADMIN_KEY = ''
YANDEX_LOGIN = ''
YANDEX_PASSWORD = ''
TOKEN = ''  # telegram token

LUNCH_TIMEOUT = 30 * 60  # таймаут для обеда
TESTIFY_TIMEOUT = 10 * 60  # таймаут после того, как сообщили диспетчеру, что водитель не отвечает

PENALTIES = {
    1: {
        "type": "warning",
        "warning": "Внимание! Вы не на линии!",
    },
    2: {
        "type": "warning",
        "warning": "Внимание! Вы не на линии! Отправьте голосовое сообщение с объяснением.",
    },
    3: {
        "type": "warning",
        "warning": "Внимание! Вы не на линии! Отправьте голосовое сообщение с объяснением.",
    },
    4: {
        "type": "call_dispatcher",
        "message": "ВНИМАНИЕ! Свяжитесь с водителем. "
                   "Водитель: {name} {surname}, находился в статусе 'ЗАНЯТ' более 20 минут!!! "
                   "Объяснительная не получена! Телефон водителя: {phone} Телеграм: {tg_name}",
        "update_timeout": 2 * 60,
    }
}

# jobs configuration
CHECK_DRIVERS_TASK_INTERVAL = 5 * 60
MAX_BUSY_MINUTES = 5  # в минутах - все остальное в секундах

# constants
VERY_VERY_BEGINING = time.monotonic()
TIME_FORMAT = '%H:%M:%S'
DEFAULT_CACHE_EXPIRE = 60 * 60 * 24  # day
CACHE_DIR = '/tmp'
DRIVERS_SECRETS_FN = 'local_storage/drivers/{name}{surname}'
DRIVER_PATH = 'local_storage/drivers/{tg_id}'
ALL_DRIVERS_FN = 'local_storage/all_drivers'
SECRETS_FN = 'local_storage/secrets'
TELEGRAM_IDS_PATH = 'local_storage/secrets/telegram_ids/{}'
PAYLOADS_PATH = 'local_storage/payloads/'
PAYLOAD_FN = 'local_storage/payloads/{}'
DRIVERS_INFO_CACHE = 'drivers_info'

try:
    from config_local import *
except ImportError:
    pass

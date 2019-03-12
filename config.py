HEADLESS = True
DEBUG = True

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
        "message": "Внимание! Вы не на линии!",
    },
    2: {
        "type": "warning",
        "message": "Внимание! Вы не на линии! Отправьте голосовое сообщение с объяснением.",
    },
    3: {
        "type": "warning",
        "message": "Внимание! Вы не на линии! Отправьте голосовое сообщение с объяснением.",
    },
    4: {
        "type": "call_dispatcher",
        "message": "ВНИМАНИЕ! Свяжитесь с водителем. Водитель: {name} {surname}, находился в статусе 'ЗАНЯТ' более 20 минут!!! Объяснительная не получена! Телефон водителя: {telephone} Телеграм: {tg_name}",
    }
}

# jobs configuration
CHECK_DRIVERS_TASK_INTERVAL = 10

# constants
TIME_FORMAT = '%H:%M:%S'
DRIVERS_SECRETS_FN = 'local_storage/drivers/{name}{surname}{tg_id}'
ALL_DRIVERS_FN = 'local_storage/all_drivers'
SECRETS_FN = 'local_storage/secrets'
OLD_DRIVERS_STATUSES_FN = 'local_storage/old_drivers_statuses'
NEW_DRIVERS_STATUSES_FN = 'local_storage/new_drivers_statuses'
TELEGRAM_IDS_PATH = 'local_storage/secrets/telegram_ids/{}'

# conversations
ASK_FOR_LUNCH = 'Попрошу отпустить вас на обед.'  # Ответ водителю, который отпрашивается на обед
CANCEL_TESTIFY = 'Слушаю.'  # Ответ водителю, когда он не захотел отправлять аудио. Возможно, хочет заново записать.

from config_local import *


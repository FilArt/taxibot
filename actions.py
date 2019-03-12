from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Voice
from telegram.bot import Bot
from telegram.update import Update

from actions_helpers import ask_register_driver, register_driver
from config import ASK_FOR_LUNCH, CANCEL_TESTIFY, LUNCH_TIMEOUT, DEBUG, SECRETS_FN, ADMIN_KEY
from fs_store import Store
from punishment import Punisher
from taxopark import Taxopark, InvalidTelephone
from utils import is_admin, is_driver
from yandex_client import YandexClient

# buttons-actions
REGISTER_DRIVER = "register_driver"
GO_TO_LUNCH = "lunch"
DRIVERS_LIST = "drivers"
UPDATE_DRIVERS_LIST = "update_drivers"

ADMIN_CHOICES = (
    REGISTER_DRIVER,
    DRIVERS_LIST,
    UPDATE_DRIVERS_LIST,
)

DRIVER_CHOICES = (
    GO_TO_LUNCH,
)

TEST_ADMIN = "test_admin"
TEST_DRIVER = "test_driver"
TEST_CHOICES = (
    TEST_ADMIN,
    TEST_DRIVER,
)


def start(bot: Bot, update: Update):
    tg_id = update.effective_user.id
    if is_admin(tg_id) and is_driver(tg_id):
        keyboard = [
            [
                InlineKeyboardButton("Admin", callback_data='test_admin'),
                InlineKeyboardButton("Driver", callback_data='test_driver'),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Test mode:', reply_markup=reply_markup)

    elif is_admin(tg_id):
        keyboard = [
            [
                InlineKeyboardButton("Зарегистрировать водителя", callback_data=REGISTER_DRIVER),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Выберите команду:', reply_markup=reply_markup)

    elif is_driver(tg_id):
        pass
    else:
        pass


def query(bot: Bot, update: Update):
    tg_id = update.effective_user.id
    choice = update.callback_query.data

    if choice in ADMIN_CHOICES:
        if choice == REGISTER_DRIVER:
            reply_markup = ask_register_driver()
            if reply_markup:
                update.message.reply_text('Выберите водителя:', reply_markup=reply_markup)
            else:
                update.effective_chat.send_message("Произошла ошибка. Список водителей пуст.")

        elif choice.startswith(REGISTER_DRIVER):
            telephone = choice.lstrip(REGISTER_DRIVER)
            response = register_driver(telephone, tg_id)
            update.effective_chat.send_message(response)

        else:
            pass


    elif choice in DRIVER_CHOICES:
        pass

    else:
        pass

    if choice == CANCEL_TESTIFY:
        update.effective_chat.send_message(choice)
        return

    driver = Taxopark.get_driver(update.effective_user.id)

    if choice == ASK_FOR_LUNCH:
        Punisher.set_timeout(driver, LUNCH_TIMEOUT)
        update.effective_chat.send_message("Иди обедай")
    elif '_' in choice:
        dispatcher_chat_id = Taxopark.get_dispatcher_chat_id()
        voice, duration = choice.split('_')
        bot.send_voice(dispatcher_chat_id, Voice(voice, duration))


def accept_testify(bot: Bot, update: Update):
    keyboard = [
        [
            InlineKeyboardButton("Мой id", callback_data='me'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Получить свой id:', reply_markup=reply_markup)

    voice = update.effective_message.voice.file_id
    duration = update.effective_message.voice.duration
    voice_reply = '{}_{}'.format(voice, duration)
    keyboard = [
        [
            InlineKeyboardButton("Отправить", callback_data=voice_reply),
            InlineKeyboardButton("Записать новое", callback_data=CANCEL_TESTIFY),
            InlineKeyboardButton("Уйти на обед", callback_data=ASK_FOR_LUNCH)
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)


def login(bot: Bot, update: Update):
    """
    Добавить новую учетную запись администратора
    """
    user_id = update.effective_user.id
    word = update.message.text.split().pop()
    if word == ADMIN_KEY:
        if is_admin(user_id):
            update.effective_chat.send_message("Уже авторизован.")
            return

        secrets = Store.load(SECRETS_FN)
        if 'admins' not in secrets:
            secrets['admins'] = [user_id]
        else:
            secrets['admins'].append(update.effective_user.id)

        Store.store(SECRETS_FN, secrets)

        update.effective_chat.send_message("Авторизация успешна.")

    else:
        update.effective_chat.send_message("Неверный пароль.")


def get_drivers_statuses(bot: Bot, update: Update):
    if not is_admin(update.effective_user.id):
        return

    yc = YandexClient()
    statuses = '\n'.join([
        f"{d['name']} {d['surname']} - {d['status']}"
        for d in yc.get_drivers_info_list()
    ])
    update.effective_chat.send_message(statuses)


def get_drivers_info(bot: Bot, update: Update):
    if DEBUG:
        yc = YandexClient()
        drivers = yc.get_drivers_info_list()
        update.effective_chat.send_message('\n'.join(
            [
                '{} {} - {} - {}'.format(d['name'], d['surname'], d['telephone'], d['status'])
                for d in drivers
            ]
        ))

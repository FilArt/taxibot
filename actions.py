from datetime import datetime, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Voice
from telegram.bot import Bot
from telegram.update import Update
from typing import List

from config import ASK_FOR_LUNCH, CANCEL_TESTIFY, LUNCH_TIMEOUT, SECRETS_FN, ADMIN_KEY
from driver import Driver, driver_info_factory
from fs_store import Store
from log import actions_logger as logger
from punishment import Punisher
from taxopark import Taxopark
from utils import is_admin, is_driver

# buttons-actions
DRIVERS_LIST = 'driversList'
ASK_REGISTER_DRIVER = 'askRegisterDriver'
REGISTER_DRIVER = "registerDriver"
GO_TO_LUNCH = "lunch"

ADMIN_CHOICES = (
    DRIVERS_LIST,
    REGISTER_DRIVER,
    ASK_REGISTER_DRIVER,
)

DRIVER_CHOICES = (
    GO_TO_LUNCH,
)

TEST_ADMIN = "testAdmin"
TEST_DRIVER = "testDriver"
TEST_CHOICES = (
    TEST_ADMIN,
    TEST_DRIVER,
)


def drivers_to_reply_markup(drivers: List[driver_info_factory], message_id: int) -> InlineKeyboardMarkup:
    """
    Вернуть список водителей в виде кнопок
    """
    def get_text(d: Driver, index):
        return f"{index + 1}. {d.name} {d.surname} {d.tg_name or ''} {d.tg_id or ''}"

    def get_callback_data(d: Driver, index):
        return f'{REGISTER_DRIVER}_{message_id}_{index}_{d.tg_name}_{d.tg_id}'

    keyboard = [
        [InlineKeyboardButton(
            get_text(d, drivers.index(d)),
            callback_data=get_callback_data(d, drivers.index(d))
        )]
        for d in drivers
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def get_my_id(bot: Bot, update: Update):
    update.effective_chat.send_message(f'Ваш Telegram id: {update.effective_user.id}')


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
                InlineKeyboardButton("Зарегистрировать водителя", callback_data=ASK_REGISTER_DRIVER),
                InlineKeyboardButton("Список водителей", callback_data=DRIVERS_LIST),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Выберите команду:', reply_markup=reply_markup)

    elif is_driver(tg_id):
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

    else:
        keyboard = [
            [
                InlineKeyboardButton("/id", callback_data='/id'),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Please choose:', reply_markup=reply_markup)


def acquire_driver_secrets(bot: Bot, update: Update):
    _, driver_index, tg_name, tg_id = update.effective_message.text.split()
    update.effective_chat.send_message(f'Регистрируем водителя {tg_name} под номером {driver_index}')
    try:
        driver = Taxopark.register_driver(int(driver_index) - 1, tg_name, int(tg_id))
        update.effective_chat.send_message(f'{driver.name} {driver.surname} {driver.tg_name} зарегистрирован.')
    except Exception as e:
        logger.exception(e)
        update.effective_chat.send_message(f'Во время регистрации возникла ошибка.')


def query(bot: Bot, update: Update):
    choice = update.callback_query.data
    command = choice.split('_')[0]

    if command in ADMIN_CHOICES or choice in ADMIN_CHOICES:
        if choice == DRIVERS_LIST:
            drivers = Taxopark.get_all_drivers_info()
            reply_markup = drivers_to_reply_markup(drivers, update.effective_message.message_id)
            update.effective_message.reply_text('Последний сохраненный список водителей:', reply_markup=reply_markup)

        elif choice == ASK_REGISTER_DRIVER:
            update.effective_chat.send_message("Получаю список водителей, ждите... (примерно 10-30 секунд)")

            try:
                if datetime.now() - Taxopark.last_update < timedelta(minutes=30):
                    drivers = Taxopark.get_all_drivers_info()
                else:
                    drivers = Taxopark.get_all_drivers_info(refresh=True)

                reply_markup = drivers_to_reply_markup(drivers, update.effective_message.message_id)
                update.effective_message.reply_text('Выберите водителя:', reply_markup=reply_markup)
            except Exception as e:
                logger.exception(e)
                update.effective_chat.send_message("Не удалось получить список водителей. Это ошибка.")

        elif command == REGISTER_DRIVER:
            _, message_id, driver_index, tg_name, tg_id = choice.split('_')

            update.effective_chat.send_message(
                'Отправьте команду `/add N @USERNAME ID`, где N - номер водителя из списка, '
                'USERNAME - имя водителя в Telegram, ID - id водителя в Telegram.\n'
                'Чтобы получить telegram id, водитель должен отправить в этот чат команду /id.'
            )

    elif choice in DRIVER_CHOICES:
        raise Exception("STOP")

    elif choice == '/id':
        get_my_id(bot, update)

    else:
        raise Exception("STOP")


def process_voice(bot: Bot, update: Update):
    choice = update.callback_query

    if choice == CANCEL_TESTIFY:
        update.effective_chat.send_message(choice)
        return

    driver = Taxopark.get_driver(tg_id=update.effective_user.id)
    # TODO: PAYLOAD UPDATING

    if choice == ASK_FOR_LUNCH:
        Punisher.set_timeout(driver, LUNCH_TIMEOUT)
        update.effective_chat.send_message("Иди обедай")
    elif '_' in choice:
        dispatcher_chat_id = Taxopark.get_dispatcher_chat_id()
        voice, duration = choice.split('_')
        bot.send_voice(dispatcher_chat_id, Voice(voice, duration))


def login(bot: Bot, update: Update):
    """
    Добавить новую учетную запись администратора
    """
    user_id = update.effective_user.id
    if is_admin(user_id):
        update.effective_chat.send_message("Уже авторизован.")
        return

    word = update.message.text.split().pop()
    if word == ADMIN_KEY:
        secrets = Store.load(SECRETS_FN)
        if 'admins' not in secrets:
            secrets['admins'] = [user_id]
        else:
            secrets['admins'].append(update.effective_user.id)

        Store.store_failsafe(SECRETS_FN, secrets)

        update.effective_chat.send_message("Авторизация успешна.")

    else:
        update.effective_chat.send_message("Неверный пароль.")

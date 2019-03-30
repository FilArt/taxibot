from telegram import Voice, Update, Bot, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters, \
    RegexHandler

from datetime import datetime

from admin_actions import cancel
from taxopark import Taxopark
from db import Config
from utils import PHONE_PATTERN

SEND_VOICE_CD = "/отправитьОбъяснительную"
STATE_PROCESS_VOICE = 0

LUNCH = "/обед"


# noinspection PyUnusedLocal
def start(bot: Bot, update: Update):
    keyboard = [[KeyboardButton("/обед")]]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите команду.", reply_markup=reply_markup)


# noinspection PyUnusedLocal
def process_voice(bot: Bot, update: Update):
    driver = Taxopark.get_driver(tg_id=update.effective_user.id)
    payload = Taxopark.get_payload(driver)
    if payload.penalty > 0:
        update.effective_chat.send_message(
            "Отправьте голосовое сообщение с объяснением.")
        return 0


def complete_process_voice(bot: Bot, update: Update):
    driver = Taxopark.get_driver(tg_id=update.effective_user.id)

    voice = update.effective_message.voice.file_id
    duration = update.effective_message.voice.duration
    dispatcher_chat_id = Taxopark.get_dispatcher_chat_id()
    bot.send_message(dispatcher_chat_id,
                     f'Объяснительная от "{driver.name} {driver.surname}"')
    bot.send_voice(dispatcher_chat_id, Voice(voice, duration))
    return ConversationHandler.END


accept_voice_handler = ConversationHandler(
    entry_points=[CommandHandler(SEND_VOICE_CD[1:], process_voice)],
    states={
        STATE_PROCESS_VOICE:
        [MessageHandler(Filters.voice, complete_process_voice)]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


def lunch_request(bot: Bot, update: Update):
    driver = Taxopark.get_driver(tg_id=update.effective_user.id)
    conf = Config.get()

    last_lunch_request_time = driver.last_lunch_request_time
    if not last_lunch_request_time or driver.lunch_count < 2:
        update.effective_chat.send_message("Обед одобрен.")
        Taxopark.add_timeout(driver, conf.lunch_timeout)
        driver.lunch_count += 1
        driver.last_lunch_request_time = datetime.now()
        driver.save()

    elif datetime.now().day - driver.last_lunch_request_time.day >= 1:
        driver.lunch_count = 0
        driver.last_lunch_request_time = datetime.now()
        driver.save()
    else:
        update.effective_chat.send_message(
            "Вы уже взяли два обеда. Это максимум в сутки.")


lunch_request_handler = CommandHandler('обед', lunch_request)


def init_registration(bot: Bot, update: Update):
    update.effective_chat.send_message(
        "Для регистрации отправьте сообщение с вашим "
        "рабочим номером телефона. Пример формата: "
        "+71234567890"
    )
    return 0


def complete_registration(bot: Bot, update: Update):
    phone = update.effective_message.text
    driver = Taxopark.get_driver_by_phone(phone)
    if driver:
        update.effective_chat.send_message("Вы уже зарегистрированы.")
        return ConversationHandler.END

    if driver is None:
        all_drivers = Taxopark.get_all_drivers()
        drivers_by_phone = {
            d.phone: d for d in all_drivers
        }
        if phone in drivers_by_phone:
            driver = drivers_by_phone[phone]
        else:
            update.effective_chat.send_message(
                "Ваш телефон не найден в базе."
                "Обратитесь к администрации таксопарка.")
            return ConversationHandler.END

    tg_name = update.effective_user.username
    tg_id = update.effective_user.id
    Taxopark.register_driver(driver, tg_name, tg_id)
    update.effective_chat.send_message("Вы зарегистрированы.")
    return ConversationHandler.END


accept_voice_handler = ConversationHandler(
    entry_points=[CommandHandler('регистрация', init_registration)],
    states={
        0: [RegexHandler(PHONE_PATTERN, complete_registration)]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

driver_handlers = (accept_voice_handler, lunch_request_handler)

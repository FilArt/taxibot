from telegram import Voice, Update, Bot, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters

from datetime import datetime

from admin_actions import cancel
from taxopark import Taxopark
from db import Config

SEND_VOICE_CD = "/sendVoice"
STATE_PROCESS_VOICE = 0

LUNCH = "/lunch"


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


def lunch_request(bot: Bot, update: Update):
    driver = Taxopark.get_driver(tg_id=update.effective_user.id)
    conf = Config.get()

    refresh_lunch_count = datetime.now().day - driver.lunch_ts.day >= 1
    if refresh_lunch_count:
        driver.lunch_count = 0
        driver.lunch_ts = datetime.now()

    if driver.lunch_count < 2:
        update.effective_chat.send_message("Обед одобрен.")
        Taxopark.add_timeout(driver, conf.lunch_timeout)
        driver.lunch_count += 1
        driver.save()
    else:
        update.effective_chat.send_message(
            "Вы уже взяли два обеда! Это максимум в сутки.")


lunch_request_handler = CommandHandler('обед', lunch_request)

accept_voice_handler = ConversationHandler(
    entry_points=[CommandHandler(SEND_VOICE_CD[1:], process_voice)],
    states={
        STATE_PROCESS_VOICE:
        [MessageHandler(Filters.voice, complete_process_voice)]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

driver_handlers = (accept_voice_handler, lunch_request_handler)

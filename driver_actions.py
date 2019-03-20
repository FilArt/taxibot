from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Voice, Update, Bot
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters

from admin_actions import cancel
from constants import LUNCH_TIMEOUT
from taxopark import Taxopark

SEND_VOICE_CD = "/sendVoice"
STATE_PROCESS_VOICE = 0

LUNCH = "/lunch"


# noinspection PyUnusedLocal
def start(bot: Bot, update: Update):
    keyboard = [[InlineKeyboardButton("Уйти на обед", callback_data=LUNCH)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите команду:", reply_markup=reply_markup)


# noinspection PyUnusedLocal
def process_voice(bot: Bot, update: Update):
    driver = Taxopark.get_driver(tg_id=update.effective_user.id)
    payload = Taxopark.get_payload(driver)
    if payload.penalty > 0:
        update.effective_chat.send_message(
            "Отправьте голосовое сообщение с объяснением."
        )
        return 0


def complete_process_voice(bot: Bot, update: Update):
    driver = Taxopark.get_driver(tg_id=update.effective_user.id)

    voice = update.effective_message.voice.file_id
    duration = update.effective_message.voice.duration
    dispatcher_chat_id = Taxopark.get_dispatcher_chat_id()
    bot.send_message(
        dispatcher_chat_id, f'Обяснительная от "{driver.name} {driver.surname}"'
    )
    bot.send_voice(dispatcher_chat_id, Voice(voice, duration))
    return ConversationHandler.END


def lunch_request(bot: Bot, update: Update):
    # TODO: добавить проверку через диспетчера
    dispatcher_id = Taxopark.get_dispatcher_chat_id()
    driver = Taxopark.get_driver(tg_id=update.effective_user.id)
    Taxopark.set_timeout(driver, LUNCH_TIMEOUT)
    bot.send_message(dispatcher_id, "NOT IMPLEMENTED")


lunch_request_handler = CommandHandler(LUNCH[1:], lunch_request)

accept_voice_handler = ConversationHandler(
    entry_points=[CommandHandler(SEND_VOICE_CD[1:], process_voice)],
    states={
        STATE_PROCESS_VOICE: [MessageHandler(Filters.voice, complete_process_voice)]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


driver_handlers = (accept_voice_handler, lunch_request_handler)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Voice, Update, Bot
from telegram.ext import ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from admin_actions import cancel
from config import LUNCH_TIMEOUT
from taxopark import Taxopark

SEND_VOICE_CD = '/sendVoice'
STATE_PROCESS_VOICE = 1

LUNCH = '/lunch'
STATE_ASK_LUNCH, STATE_ACCEPT_LUNCH_REQUEST = range(2)


def start(bot: Bot, update: Update):
    keyboard = [[InlineKeyboardButton("Отправить объяснительную", callback_data=SEND_VOICE_CD),
                 InlineKeyboardButton("Уйти на обед", callback_data=LUNCH)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите команду:', reply_markup=reply_markup)


def process_voice(bot: Bot, update: Update):
    update.effective_chat.send_message("Отправьте голосовое сообщение с объяснением.")
    return 0


def complete_process_voice(bot: Bot, update: Update):
    try:
        voice = update.effective_message.voice.file_id
        duration = update.effective_message.voice.duration
        dispatcher_chat_id = Taxopark.get_dispatcher_chat_id()
        bot.send_voice(dispatcher_chat_id, Voice(voice, duration))
    except:
        update.effective_chat.send_message("Произошла внутренняя ошибка. Начните операцию сначала.")
    return ConversationHandler.END


def lunch_request(bot: Bot, update: Update):
    # TODO: добавить проверку через диспетчера
    dispatcher_id = Taxopark.get_dispatcher_chat_id()
    driver = Taxopark.get_driver()
    Taxopark.set_timeout(driver.name, driver.surname, LUNCH_TIMEOUT)
    bot.send_message(dispatcher_id, "NOT IMPLEMENTED")


accept_voice_handler = ConversationHandler(
    entry_points=[CommandHandler(SEND_VOICE_CD, process_voice)],
    states={
        0: [MessageHandler(Filters.voice, complete_process_voice)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)


driver_handlers = (
    accept_voice_handler,
)

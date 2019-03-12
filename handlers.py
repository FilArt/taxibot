from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler
from telegram.ext.filters import Filters

from actions import login, start, query, process_voice
from config import DEBUG

login_handler = CommandHandler('login', login)
voice_msg_handler = MessageHandler(Filters.voice, process_voice)
start_handler = CommandHandler('start', start)
query_handler = CallbackQueryHandler(query)

handlers = (
    login_handler,
    voice_msg_handler,
    start_handler,
    query_handler,
)

if DEBUG:
    handlers = (
        *handlers,
    )


def handling_handlers(dispatcher):
    for handler in handlers:
        dispatcher.add_handler(handler)

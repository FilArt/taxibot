from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler
from telegram.ext.filters import Filters

from actions import (
    login, get_drivers_statuses, get_drivers_info, accept_testify, start)
from config import DEBUG

login_handler = CommandHandler('login', login)
statuses_handler = CommandHandler('statuses', get_drivers_statuses)
voice_msg_handler = MessageHandler(Filters.voice, accept_testify)

start_handler = CommandHandler('start', start)
query_handler = CallbackQueryHandler(start)

test_func = CommandHandler('drivers', get_drivers_info)

handlers = (
    login_handler,
    statuses_handler,
    voice_msg_handler,
    start_handler,
    query_handler,
)

if DEBUG:
    handlers = (
        *handlers,
        test_func,
    )


def handling_handlers(dispatcher):
    for handler in handlers:
        dispatcher.add_handler(handler)

from telegram.ext import CommandHandler

from actions import login, start, get_id
from admin_actions import admin_handlers
from driver_actions import driver_handlers
from dispatcher_actions import dispatcher_handlers

login_handler = CommandHandler("login", login)
start_handler = CommandHandler("start", start)
id_handler = CommandHandler("id", get_id)

handlers = (id_handler, login_handler, start_handler,
            *admin_handlers, *driver_handlers, *dispatcher_handlers)


def handling_handlers(dispatcher):
    for handler in handlers:
        dispatcher.add_handler(handler)

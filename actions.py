from telegram.bot import Bot
from telegram.update import Update

from action_classes import get_action_class
from taxopark import Taxopark


def login(bot: Bot, update: Update):
    """
    Добавить новую учетную запись администратора
    """
    tg_id = update.effective_user.id
    if tg_id in Taxopark.get_registered_drivers_tg_ids():
        update.effective_chat.send_message("Уже авторизован.")
        return

    action_class = get_action_class(bot, update)
    action_class.login()


def start(bot: Bot, update: Update):
    action_class = get_action_class(bot, update)
    if action_class:
        action_class.start()


def query(bot: Bot, update: Update):
    choice = update.callback_query.data
    action_class = get_action_class(bot, update)
    if action_class:
        action_class.query(choice)


def process_voice(bot: Bot, update: Update):
    choice = update.callback_query
    action_class = get_action_class(bot, update)
    if action_class:
        action_class.process_voice(choice)


def add_driver(bot: Bot, update: Update):
    action_class = get_action_class(bot, update)
    if action_class:
        action_class.add_driver()

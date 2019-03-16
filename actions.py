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

    action_classes = get_action_class(bot, update)
    for ac in action_classes:
        ac.login()


def start(bot: Bot, update: Update):
    action_classes = get_action_class(bot, update)
    for ac in action_classes:
        ac.start()


def query(bot: Bot, update: Update):
    choice = update.callback_query.data
    action_classes = get_action_class(bot, update)
    for ac in action_classes:
        ac.query(choice)


def process_voice(bot: Bot, update: Update):
    choice = update.callback_query
    action_classes = get_action_class(bot, update)
    for ac in action_classes:
        ac.process_voice(choice)


def add_driver(bot: Bot, update: Update):
    action_classes = get_action_class(bot, update)
    for ac in action_classes:
        ac.add_driver()

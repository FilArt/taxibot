from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.bot import Bot
from telegram.ext import ConversationHandler
from telegram.update import Update

import admin_actions
import driver_actions
from config import ADMIN_KEY
from taxopark import Taxopark


def login(bot: Bot, update: Update):
    """
    Добавить новую учетную запись администратора
    """
    words = update.effective_message.text.split()
    if len(words) == 2 and words[1] == ADMIN_KEY:
        tg_id = update.effective_user.id
        if Taxopark.is_admin(tg_id):
            update.effective_chat.send_message('Вы уже зарегистрированы.')
        else:
            Taxopark.register_admin(tg_id)
            update.effective_chat.send_message('Успешно зарегистрирован.')


def get_id(bot: Bot, update: Update):
    update.effective_chat.send_message(update.effective_user.id)


def start(bot: Bot, update: Update):
    tg_id = update.effective_user.id
    if Taxopark.is_driver(tg_id):
        driver_actions.start(bot, update)
    elif Taxopark.is_admin(tg_id):
        admin_actions.start(bot, update)
    else:
        reply_keyboard = [['/id']]

        update.message.reply_text(
            'Выберите команду:',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

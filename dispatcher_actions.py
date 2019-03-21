from telegram import Bot, Update
from telegram.ext import CallbackQueryHandler

from taxopark import Taxopark
from db import Config


def let_go_for_lunch(bot: Bot, update: Update):
    if update.effective_user.id != Taxopark.get_dispatcher_chat_id():
        return

    query = update.callback_query
    data = query.data
    answer = {'+': 'Yes', '-': 'No'}[data[0]]
    driver_id = data[1:]
    driver = Taxopark.get_driver(driver_id=driver_id)
    conf = Config.get()
    tout = conf.lunch_timeout

    if answer == 'Yes':
        Taxopark.set_timeout(driver, tout)
        bot.send_message(driver.tg.id, f"Обед одобрен. Добавлено {tout} минут свободного времени.")
    else:
        bot.send_message(driver.tg.id, "Ваш запрос на обед отклонен.")

    update.callback_query.answer("Ваше решение передано водителю.")


lunch_handler = CallbackQueryHandler(let_go_for_lunch)

dispatcher_handlers = (
    lunch_handler,
)

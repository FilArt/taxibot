from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from taxopark import Taxopark, InvalidTelephone


def ask_register_driver() -> InlineKeyboardMarkup:
    """
    Админ нажал кнопку "добавить водителя". Нужно вернуть ему список
    """
    drivers_info = Taxopark.get_unregistered_drivers()
    keyboard = [
        [InlineKeyboardButton(
            f"{d.name} {d.surname}",
            callback_data=d.telephone
        )]
        for d in drivers_info
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def register_driver(telephone: str, tg_id: str) -> str:
    """
    Админ выбрал водителя, которого хочет зарегистрировать
    """
    try:
        Taxopark.register_driver(telephone, tg_id)
        return "Водитель зарегистрирован. Проверьте список."
    except InvalidTelephone:
        return "Такого номера в базе не найдено. Попробуйте обновить список водителей."\
               "Пример формата номера: +79215615422"

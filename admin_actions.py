from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQuery

from utils import is_admin


def admin_actions(bot: Bot, update: Update):
    """
    Админка
    """
    if not is_admin(update.effective_user.id):
        return

    keyboard = [
        [
            InlineKeyboardButton("Добавить водителя", callback_data=0),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Доступные команды:', reply_markup=reply_markup)


def handle_admin_action(bot: Bot, update: Update):
    choice = update.callback_query.data

    if choice == 0:
        keyboard = [
            [
                InlineQuery("Ра", callback_data=0),
                # InlineKeyboardButton("Записать новое", callback_data=1),
                # InlineKeyboardButton("Уйти на обед", callback_data=2)
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Доступные команды:', reply_markup=reply_markup)
        return


# def add_driver(bot: Bot, update: Update):
#     """
#     Регаем водителя
#     """
#     driver_tg_id = update.effective_user.id
#     if is_authenticated(driver_tg_id):
#         update.effective_chat.send_message("Уже авторизован.")
#         return
#
#     driver_tg_name = update.effective_user.name
#
#     yc = YandexClient()
#
#     job_phone = update.message.text.split().pop()  # маппим по тлф
#     drivers_info_list = yc.get_drivers_info_list()
#     driver_info = [d_info for d_info in drivers_info_list if d_info['telephone'] == job_phone]
#
#     if driver_info:
#         driver_info = driver_info.pop()
#         driver_info['tg_name'] = driver_tg_name
#         driver_info['tg_id'] = driver_tg_id
#         driver = Driver(driver_info)
#         register_driver(driver)
#         update.effective_chat.send_message("Вы успешно зарегистрированы.")
#         update.effective_chat.send_message('Проверьте свои данные:\n{}'.format(
#             '\n'.join((driver_info['name'], driver_info['surname'])),
#         ))
#     else:
#         update.effective_chat.send_message("Не удалось найти ваш номер. Пример формата: +71234567890")

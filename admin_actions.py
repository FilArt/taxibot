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

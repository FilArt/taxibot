from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Bot,
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    RegexHandler,
    MessageHandler,
    Filters,
)

from db import Config
from taxopark import Taxopark

DRIVERS_CACHE = {"add": {}, "modify": {}}
OPTIONS_CACHE = {}


def start(bot: Bot, update: Update):
    reply_keyboard = [[CD_ADD_DRIVER, CD_MODIFY_DRIVER, CD_CONFIG]]

    update.message.reply_text(
        "Выберите команду:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )


# noinspection PyUnusedLocal
def cancel(bot: Bot, update: Update):
    update.message.reply_text("Операция отменена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


""" BEGIN CONFIG CONVERSATION """
CD_CONFIG = "/config"
STATE_SHOW_CONFIG, STATE_CHOOSE_OPTION, STATE_ACCEPT_OPTION = range(3)


# noinspection PyUnusedLocal
def show_config(bot: Bot, update: Update):
    if not Taxopark.is_admin(update.effective_user.id):
        return

    conf = Config.get()
    options = [
        (key, getattr(conf, key)) for key in conf if key in Config.translation_map
    ]
    keyboard = [
        [
            InlineKeyboardButton(
                f"{Config.translation_map[key]}: {val}", callback_data=key
            )
        ]
        for key, val in options
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message("Выберите опцию:", reply_markup=reply_markup)
    return STATE_CHOOSE_OPTION


def choose_option(bot: Bot, update: Update):
    option = update.callback_query.data
    OPTIONS_CACHE[update.effective_user.id] = option
    update.effective_chat.send_message(
        f"Выбрана опция {option}. Введите новое значение."
    )
    update.callback_query.answer("Processing...")
    return STATE_ACCEPT_OPTION


# noinspection PyUnusedLocal
def accept_option(bot: Bot, update: Update):
    new_value = update.effective_message.text
    config = Config.get()
    option = OPTIONS_CACHE[update.effective_user.id]
    if option == "max_busy_time":
        config.set_max_busy_time(int(new_value))
    elif option == "dispatcher_chat_id":
        config.set_dispatcher_chat_id(int(new_value))
    elif option == "check_drivers_interval":
        config.set_check_drivers_interval(int(new_value))
    elif option == "lunch_timeout":
        config.set_lunch_timeout(int(new_value))
    update.effective_chat.send_message(
        f"Опции {option} установлено новое значение: {new_value}.")
    return ConversationHandler.END


config_handler = ConversationHandler(
    entry_points=[CommandHandler(CD_CONFIG[1:], show_config)],
    states={
        STATE_CHOOSE_OPTION: [CallbackQueryHandler(choose_option)],
        STATE_ACCEPT_OPTION: [MessageHandler(Filters.text, accept_option)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
""" END CONFIG CONVERSATION """
""" BEGIN ADD DRIVER CONVERSATION """
CD_ADD_DRIVER = "/addDriver"
STATE_ASK_FOR_TG_CREDS, STATE_REGISTER_DRIVER = range(2)


def add_drivers(bot: Bot, update: Update):
    if not Taxopark.is_admin(update.effective_user.id):
        return

    update.effective_chat.send_message(
        "Получаю список незарегистрированных водителей, ждите...")
    drivers = {
        driver.phone: driver
        for driver in Taxopark.get_unregistered_drivers()
    }
    DRIVERS_CACHE["add"][update.effective_user.id] = drivers
    keyboard = [[
        InlineKeyboardButton(
            f"{d.name}  {d.surname}", callback_data=f"{phone}")
    ] for phone, d in drivers.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(
        "Выберите водителя:", reply_markup=reply_markup)
    return STATE_ASK_FOR_TG_CREDS


def ask_for_tg_creds(bot: Bot, update: Update):
    query = update.callback_query
    query.answer("Processing...")
    unique_id = query.data
    driver = DRIVERS_CACHE["add"][update.effective_user.id].pop(unique_id)
    DRIVERS_CACHE["add"][update.effective_user.id] = driver
    update.effective_chat.send_message(
        f'Для регистрации водителя "{driver.name} {driver.surname}" введите '
        'его имя пользователя Telegram и Telegram ID в формате "@username 123456789"'
    )
    return STATE_REGISTER_DRIVER


def register_driver(bot: Bot, update: Update):
    driver = DRIVERS_CACHE["add"].pop(update.effective_user.id)
    tg_name, tg_id = update.message.text.split()
    Taxopark.register_driver(driver, tg_name, tg_id)
    update.effective_chat.send_message(
        "Водитель зарегистрирован. Проверьте данные:\n"
        f"{driver.name} {driver.surname}\n"
        f"Рабочий телефон: {driver.phone}\n"
        f"Telegram username: {driver.tg.name}\n"
        f"Telegram ID: {driver.tg.id}")
    return ConversationHandler.END


add_driver_handler = ConversationHandler(
    entry_points=[CommandHandler(CD_ADD_DRIVER[1:], add_drivers)],
    states={
        STATE_ASK_FOR_TG_CREDS: [CallbackQueryHandler(ask_for_tg_creds)],
        STATE_REGISTER_DRIVER:
        [RegexHandler(r"^@.{1,40} \d{3,11}$", register_driver)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
""" END ADD DRIVER CONVERSATION """
""" BEGIN MODIFY DRIVER CONVERSATION """
CD_MODIFY_DRIVER = "/modifyDriver"
STATE_SHOW_DRIVER, STATE_ASK_MODIFY, STATE_COMPLETE_MODIFY = range(3)


def registered_drivers_list(bot: Bot, update: Update):
    if not Taxopark.is_admin(update.effective_user.id):
        return

    drivers = Taxopark.get_registered_drivers()

    if not drivers:
        update.effective_chat.send_message(
            "Ни одного водителя не зарегистрировано."
            "Отмена операции.")
        return

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            f"{drivers.index(d) + 1}. {d.name} {d.surname} {d.tg.name}",
            callback_data=f"{d.id}",
        )
    ] for d in drivers])
    update.effective_chat.send_message(
        "Список зарегистрированных водителей:", reply_markup=reply_markup)
    return STATE_SHOW_DRIVER


def show_driver(bot: Bot, update: Update):
    driver_id = update.callback_query.data
    driver = Taxopark.get_driver(driver_id)
    attributes = ("tg_name", "tg_id")
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            f"{attribute}: {getattr(driver, attribute)}",
            callback_data=f"{driver_id} {attribute}",
        )
    ] for attribute in attributes])
    update.effective_chat.send_message(
        "Выберите аттрибут для изменения:", reply_markup=reply_markup)
    update.callback_query.answer("Processing...")
    return STATE_ASK_MODIFY


def ask_modify_driver(bot: Bot, update: Update):
    driver_id, attribute = update.callback_query.data.split()
    DRIVERS_CACHE["modify"][update.effective_user.id] = driver_id, attribute
    update.effective_chat.send_message(
        f'Для изменения аттрибута "{attribute}" отправьте сообщение '
        'с новым значением в формате "NEW=XXX", где ХХХ - новое значение.')
    update.callback_query.answer("Processing...")
    return STATE_COMPLETE_MODIFY


def complete_modify_driver(bot: Bot, update: Update):
    new_value = update.effective_message.text.split("=")[1]
    driver_id, attribute = DRIVERS_CACHE["modify"][update.effective_user.id]
    driver = Taxopark.get_driver(driver_id)
    if attribute == "tg_name":
        Taxopark.update_tg_name(driver, new_value)
        new_value = driver.tg.name
    elif attribute == "tg_id":
        Taxopark.update_tg_id(driver, new_value)
        new_value = driver.tg.id

    update.effective_chat.send_message(
        f"Значение {attribute} водителя {driver.name} {driver.surname} "
        f"изменено на {new_value}.")
    return ConversationHandler.END


modify_driver_handler = ConversationHandler(
    entry_points=[
        CommandHandler(CD_MODIFY_DRIVER[1:], registered_drivers_list)
    ],
    states={
        STATE_SHOW_DRIVER: [CallbackQueryHandler(show_driver)],
        STATE_ASK_MODIFY: [CallbackQueryHandler(ask_modify_driver)],
        STATE_COMPLETE_MODIFY:
        [RegexHandler("^NEW.+$", complete_modify_driver)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
""" END MODIFY DRIVER CONVERSATION """

admin_handlers = (add_driver_handler, modify_driver_handler, config_handler)

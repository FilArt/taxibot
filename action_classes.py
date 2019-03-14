from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Bot, Update, Voice
from typing import List, Union

from config import LUNCH_TIMEOUT, ADMIN_KEY, SECRETS_FN
from driver import Driver
from fs_store import Store
from log import actions_logger as logger
from taxopark import Taxopark
from utils import is_admin, is_driver


class BaseAction:
    def __init__(self, bot: Bot, update: Update, tg_id: int):
        self.bot = bot
        self.update = update
        self.tg_id = tg_id

    def login(self):
        word = self.update.message.text.split().pop()
        if word == ADMIN_KEY:
            secrets = Store.load(SECRETS_FN)

            if 'admins' not in secrets:
                secrets['admins'] = [self.tg_id]
            else:
                secrets['admins'].append(self.tg_id)

            Store.store_failsafe(SECRETS_FN, secrets)
            self.update.effective_chat.send_message("Авторизация успешна.")

        else:
            self.update.effective_chat.send_message("Неверный пароль.")

    def start(self):
        keyboard = [[InlineKeyboardButton("/id", callback_data='/id')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        self.update.message.reply_text('Please choose:', reply_markup=reply_markup)

    def query(self, choice: str):
        if choice == '/id':
            self.update.effective_chat.send_message(f'Ваш Telegram id: {self.tg_id}')


class AdminAction(BaseAction):
    DRIVERS_LIST = 'driversList'
    ASK_REGISTER_DRIVER = 'askRegisterDriver'
    REGISTER_DRIVER = "registerDriver"
    GO_TO_LUNCH = "lunch"

    def start(self):
        keyboard = [[InlineKeyboardButton("Зарегистрировать водителя", callback_data=self.ASK_REGISTER_DRIVER),
                     InlineKeyboardButton("Список водителей", callback_data=self.DRIVERS_LIST)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        self.update.message.reply_text('Выберите команду:', reply_markup=reply_markup)

    def query(self, choice: str):
        if choice == self.DRIVERS_LIST:
            self._driver_list()

        elif choice == self.ASK_REGISTER_DRIVER:
            self._ask_register_driver()

        elif choice.startswith(self.REGISTER_DRIVER):
            _, message_id, driver_index, tg_name, tg_id = choice.split('_')

            self.update.effective_chat.send_message(
                'Отправьте команду `/add N @USERNAME ID`, где N - номер водителя из списка, '
                'USERNAME - имя водителя в Telegram, ID - id водителя в Telegram.\n'
                'Чтобы получить telegram id, водитель должен отправить в этот чат команду /id.'
            )

    def _driver_list(self):
        drivers_info = Taxopark.get_all_drivers_info()
        drivers = []
        for driver_info in drivers_info:
            name, surname = driver_info.name, driver_info.surname
            if Taxopark.is_registered(name, surname):
                driver = Taxopark.get_driver(name=driver_info.name, surname=driver_info.surname)
            else:
                driver = Driver(driver_info)
            drivers.append(driver)

        reply_markup = self._drivers_to_reply_markup(drivers, self.update.effective_message.message_id)
        self.update.effective_message.reply_text('Последний сохраненный список водителей:', reply_markup=reply_markup)

    def _ask_register_driver(self):
        self.update.effective_chat.send_message("Получаю список водителей, ждите... (примерно 10-30 секунд)")
        drivers = Taxopark.get_all_drivers_info()
        reply_markup = self._drivers_to_reply_markup(drivers, self.update.effective_message.message_id)
        self.update.effective_message.reply_text('Выберите водителя:', reply_markup=reply_markup)

    def _drivers_to_reply_markup(self, drivers: List[Driver], message_id: int) -> InlineKeyboardMarkup:
        """
        Вернуть список водителей в виде кнопок
        """
        def get_text(d: Driver, index):
            return f"{index + 1}. {d.name} {d.surname} {d.tg_name or ''} {d.tg_id or ''}"

        def get_callback(d: Driver, index):
            return f'{self.REGISTER_DRIVER}_{message_id}_{index}_{d.tg_name}_{d.tg_id}'

        return InlineKeyboardMarkup(
            [[InlineKeyboardButton(get_text(d, drivers.index(d)), callback_data=get_callback(d, drivers.index(d)))]
             for d in drivers]
        )


class DriverAction(BaseAction):
    LUNCH = "lunch"
    CANCEL_TESTIFY = 'cancelTestify'

    def start(self):
        keyboard = [[InlineKeyboardButton("Мой id", callback_data='me')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        self.update.message.reply_text('Получить свой id:', reply_markup=reply_markup)

        voice = self.update.effective_message.voice.file_id
        duration = self.update.effective_message.voice.duration
        voice_reply = '{}_{}'.format(voice, duration)
        keyboard = [[InlineKeyboardButton("Отправить", callback_data=voice_reply),
                     # TODO: добавить в конфиг
                     InlineKeyboardButton("Записать новое", callback_data='NOT IMPLEMENTED'),
                     InlineKeyboardButton("Уйти на обед", callback_data='NOT IMPLEMENTED')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        self.update.message.reply_text('Please choose:', reply_markup=reply_markup)

    def add_driver(self):
        _, driver_index, tg_name, tg_id = self.update.effective_message.text.split()
        self.update.effective_chat.send_message(f'Регистрируем водителя {tg_name} под номером {driver_index}')
        try:
            driver = Taxopark.register_driver(int(driver_index) - 1, tg_name, int(tg_id))
            self.update.effective_chat.send_message(f'{driver.name} {driver.surname} {driver.tg_name} зарегистрирован.')
        except Exception as e:
            logger.exception(e)
            self.update.effective_chat.send_message('Во время регистрации возникла ошибка.')

    def process_voice(self, choice: str):
        if choice == self.CANCEL_TESTIFY:
            self.update.effective_chat.send_message(choice)

        elif choice == self.LUNCH:
            self._lunch_request()

        elif '_' in choice:
            dispatcher_chat_id = Taxopark.get_dispatcher_chat_id()
            voice, duration = choice.split('_')
            self.bot.send_voice(dispatcher_chat_id, Voice(voice, duration))

    def _lunch_request(self):
        # TODO: добавить проверку через диспетчера
        dispatcher_id = Taxopark.get_dispatcher_chat_id()
        driver = Taxopark.get_driver(tg_id=self.tg_id)
        Taxopark.set_timeout(driver, LUNCH_TIMEOUT)
        self.bot.send_message(dispatcher_id, "NOT IMPLEMENTED")


def get_action_class(bot: Bot, update: Update) -> Union[BaseAction, DriverAction, AdminAction]:
    tg_id = update.effective_user.id
    if is_admin(tg_id):
        return AdminAction(bot, update, tg_id)
    elif is_driver(tg_id):
        return DriverAction(bot, update, tg_id)
    else:
        return BaseAction(bot, update, tg_id)

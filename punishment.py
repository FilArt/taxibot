from telegram import Bot

from config import PENALTIES
from db import Driver
from log import punish_logger as logger
from taxopark import Taxopark
from utils import merge_with_pattern


class Punishment:
    """
    Класс для управления наказаниями
    """
    def __init__(self, penalty: int):
        self.penalty = PENALTIES[penalty]
        self.type = self.penalty['type']
        self.message = self.penalty.get('message')
        self.update_timeout = self.penalty.get('update_timeout')

    def __str__(self):
        return str(self.penalty)

    def __repr__(self):
        return self.__str__()

    @property
    def is_warning(self):
        return self.type == 'warning'

    @property
    def is_call_dispatcher(self):
        return self.type == 'call_dispatcher'


class Punisher:
    def __init__(self, bot: Bot):
        self._bot = bot

    def punish_driver(self, driver: Driver):
        name, surname = driver.name, driver.surname
        if not Taxopark.is_registered(driver):
            logger.info('skip unregistered driver %s %s', name, surname)
            return

        payload = Taxopark.get_payload(driver.name, driver.surname)
        payload.update_timeout()
        if payload.timeout is not None:
            logger.info('skip driver %s %s which has timeout', name, surname)
            return

        punishment = Punishment(payload.penalty)
        if punishment.is_warning:
            self._send_warning(punishment.message, driver)
        elif punishment.is_call_dispatcher:
            self._call_dispatcher(punishment.message, driver)
            Taxopark.set_timeout(driver.name, driver.surname, punishment.update_timeout)

    def _send_warning(self, warning, driver: Driver):
        self._bot.send_message(driver.tg.id, warning)
        logger.info('warning for %s %s sent', driver.name, driver.surname)

    def _call_dispatcher(self, message, driver: Driver):
        message = merge_with_pattern(message, driver.to_dict())
        self._bot.send_message(Taxopark.get_dispatcher_chat_id(), message)
        logger.info("dispatcher informed about %s %s", driver.name, driver.surname)

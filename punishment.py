from datetime import datetime
from telegram import Bot, ReplyKeyboardMarkup

from config import PENALTIES
from db import Driver, Config
from driver_actions import SEND_VOICE_CD
from log import punish_logger as logger
from taxopark import Taxopark
from utils import merge_with_pattern


class Punishment:
    """
    Класс для управления наказаниями
    """

    def __init__(self, i: int):
        self._i = i
        self.penalty = PENALTIES[i]
        self.type = self.penalty["type"]
        self.message = self.penalty.get("message")
        self.update_timeout = self.penalty.get("update_timeout")
        self._button = self.penalty.get("button")

    def __str__(self):
        return str(self.penalty)

    def __repr__(self):
        return self.__str__()

    @property
    def button(self):
        if self._button:
            return ReplyKeyboardMarkup([[SEND_VOICE_CD]],
                                       one_time_keyboard=True)

    @property
    def is_warning(self):
        return self.type == "warning"

    @property
    def is_call_dispatcher(self):
        return self.type == "call_dispatcher"


class Punisher:
    def __init__(self, bot: Bot):
        self._bot = bot

    def punish_driver(self, driver: Driver):
        conf = Config.get()

        name, surname, status = driver.name, driver.surname, driver.status.value

        if not driver.busy:
            logger.info('driver %s %s not busy, his status is - "%s"', name,
                        surname, status)
            return

        busy_minutes = round((datetime.utcnow() - driver.status.set_at).total_seconds() / 60)
        if busy_minutes <= conf.max_busy_time:
            logger.info(
                "skip driver %s %s - he is busy for only %i minutes. "
                "it is acceptable",
                name,
                surname,
                busy_minutes,
            )
            return

        if not Taxopark.is_registered(driver):
            logger.info("skip unregistered driver %s %s", name, surname)
            return

        payload = Taxopark.get_payload(driver)
        payload.update_timeout()
        if not payload.timeout or payload.timeout < 1:
            logger.info("skip driver %s %s which has timeout %i", name, surname, payload.timeout)
            return

        payload.increment_penalties()

        punishment = Punishment(payload.penalty)
        if punishment.is_warning:
            self._send_warning(
                punishment.message, driver, reply_markup=punishment.button)
        elif punishment.is_call_dispatcher:
            self._call_dispatcher(punishment.message, driver)
            Taxopark.add_timeout(driver, int(punishment.update_timeout))

    def _send_warning(self, warning, driver: Driver, reply_markup=None):
        self._bot.send_message(
            driver.tg.id, warning, reply_markup=reply_markup)
        logger.info("warning for %s %s sent", driver.name, driver.surname)

    def _call_dispatcher(self, message, driver: Driver):
        message = merge_with_pattern(message, driver.to_dict())
        self._bot.send_message(Taxopark.get_dispatcher_chat_id(), message)
        logger.info("dispatcher informed about %s %s", driver.name,
                    driver.surname)

from typing import List

from config import PENALTIES
from payload import Payload
from taxopark import Taxopark
from log import punishment_logger as logger


class Punisher:
    """
    Класс для раздачи пиздюлей
    """
    @classmethod
    def fetch_and_update_busy_drivers_payloads(cls) -> List[Payload]:
        drivers_info = Taxopark.get_drivers_info_from_map()

        payloads = []
        for driver_info in drivers_info:
            name, surname = driver_info.name, driver_info.surname
            if not Taxopark.is_registered(name, surname):
                logger.info('skip unregistered driver %s %s', name, surname)
                continue

            if Payload.exists(name, surname):
                payload = Taxopark.get_payload(name, surname)
                payload.increment_penalties()
            else:
                payload = Payload(name, surname, penalties=1)
                payload.save()

            payloads.append(payload)
        return payloads


class Punishment:
    """
    Класс для управления наказаниями
    """
    def __init__(self, penalty: int):
        self.penalty = PENALTIES[penalty]

    def __str__(self):
        return str(self.penalty)

    def __repr__(self):
        return self.__str__()

    @property
    def is_warning(self):
        return self.penalty['type'] == 'warning'

    @property
    def is_call_dispatcher(self):
        return self.penalty['type'] == 'call_dispatcher'

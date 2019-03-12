import os
from datetime import datetime
from typing import Dict, List

from config import PENALTIES, OLD_DRIVERS_STATUSES_FN, CHECK_DRIVERS_TASK_INTERVAL, NEW_DRIVERS_STATUSES_FN
from fs_store import Store


class Payload:
    """
    Протокол хранения данных о занятых водителях
    """

    def __init__(self, name, surname, telephone, penalties: int, timeout: int = None, timeout_set_at: datetime = None):
        self.name = name
        self.surname = surname
        self.telephone = telephone
        self.penalties = penalties
        self.timeout = timeout
        self.timeout_set_at = timeout_set_at

    def __str__(self):
        return f'{self.name}_{self.surname}'

    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_str(cls, string):
        return cls(*string.split('_'))


class Punisher:
    """
    Класс для раздачи пиздюлей
    """
    @classmethod
    def set_timeout(cls, driver, timeout: int):
        local_payloads = Punisher._get_old_busy_payloads()
        for i in range(len(local_payloads)):
            payload = local_payloads[i]
            if payload.telephone == driver.telephone:
                local_payloads[i].timeout = timeout
                local_payloads[i].timeout_set_at = datetime.now()
                break

        Store.store(OLD_DRIVERS_STATUSES_FN, local_payloads)

    @classmethod
    def fetch_and_update_busy_drivers_payloads(cls, selenium_client):
        old_busy_payloads = cls._get_old_busy_payloads()
        new_busy_payloads = cls._get_new_busy_payloads(selenium_client)

        current_busy_payloads = []
        for payload in new_busy_payloads:


            # найдем payload этого же водителя среди старых, маппим по тлф
            old_payload = [p for p in old_busy_payloads if p.telephone == payload.telephone]

            if old_payload:
                payload = cls._merge_payloads(old_payload.pop(), payload)

            current_busy_payloads.append(payload)

        Store.store(OLD_DRIVERS_STATUSES_FN, current_busy_payloads)
        return current_busy_payloads

    @staticmethod
    def _merge_payloads(old: Payload, new: Payload) -> Payload:
        """
        Объединяет payload-ы из разных источников (локального и АПИ)
        Важная хуйня, не ошибится с обработкой таймаута
        """
        def update_timeout(old_timeout, when_timeout_was_set) -> int:
            now = datetime.now()
            assert now > when_timeout_was_set

            passed_seconds = now - when_timeout_was_set
            assert passed_seconds - old_timeout < CHECK_DRIVERS_TASK_INTERVAL, "По идее такого не должно быть"

            if passed_seconds >= old_timeout:
                return 0

            return old_timeout - passed_seconds

        assert old.surname == new.surname, "Нельзя мержить payload-ы разных таксистов"  # однофамильцы пох
        assert old.name == new.name, "Нельзя мержить payload-ы разных таксистов"
        assert old.telephone == new.telephone, "Нельзя мержить payload-ы разных таксистов"
        assert new.timeout is new.timeout_set_at is None, "У payload-а из АПИ не может быть timeout-а"

        name = old.name
        surname = old.surname
        telephone = old.telephone
        penalties = old.penalties + 1
        timeout = old.timeout
        if timeout in (None, 0):
            return Payload(name=name, surname=surname, telephone=telephone, penalties=penalties)

        when_timeout_was_set = old.timeout_set_at
        new_timeout = update_timeout(timeout, when_timeout_was_set)

        return Payload(name=name, surname=surname, telephone=telephone,
                       penalties=penalties, timeout=new_timeout,
                       timeout_set_at=when_timeout_was_set)

    @staticmethod
    def _get_old_busy_payloads() -> List[Payload]:
        """
        Достать payloads из локального хранилища
        """
        try:
            return Store.load(OLD_DRIVERS_STATUSES_FN)
        except FileNotFoundError:
            return []

    @staticmethod
    def _get_new_busy_payloads(selenium_client, way='selenium') -> List[Payload]:
        """
        Данные из диспетчерской
        """
        if way == 'selenium':
            # drivers = Store.load_json(NEW_DRIVERS_STATUSES_FN)
            drivers = selenium_client.get_drivers_from_map()
            return [
                Payload(name=d['name'], surname=d['surname'], telephone=d['telephone'], penalties=1)
                for d in drivers
                if d['status'] == 'Busy' and int(d['minutes']) >= 5
            ]
        else:
            raise NotImplementedError


class Punishment:
    """
    Класс для управления наказаниями
    """
    def __init__(self, penalty: int):
        self.penalty = PENALTIES[penalty]

    @property
    def is_warning(self):
        return self.penalty['type'] == 'warning'

    @property
    def is_call_dispatcher(self):
        return self.penalty['type'] == 'call_dispatcher'

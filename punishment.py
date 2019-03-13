import os

from datetime import datetime
from typing import List, Optional, Any

from config import (PENALTIES, OLD_DRIVERS_STATUSES_FN, CHECK_DRIVERS_TASK_INTERVAL, YANDEX_LOGIN, YANDEX_PASSWORD,
                    MAX_BUSY_MINUTES, PAYLOADS_PATH, PAYLOAD_FN)
from fs_store import Store
from selenium_client import SeleniumClient


class Payload:
    """
    Протокол хранения данных о занятых водителях
    """

    def __init__(self, phone, penalties: int, timeout: int = None, timeout_set_at: datetime = None):
        self.phone = phone
        self.penalties = penalties
        self.timeout = timeout
        self.timeout_set_at = timeout_set_at

    @classmethod
    def get_payload(cls, phone) -> Optional['Payload']:
        path = PAYLOAD_FN.format(phone=phone[1:])
        if os.path.exists(path):
            return Store.load(path)
        return None

    def save(self):
        Store.store_failsafe(PAYLOAD_FN.format(phone=self.phone[1:]), self)

    def update_timeout(self):
        timeout_seconds = self.timeout * 60
        now = datetime.now()
        assert now > self.timeout_set_at

        passed_seconds = (now - self.timeout_set_at).seconds

        if passed_seconds >= timeout_seconds:
            self.timeout = None
        else:
            self.timeout = (timeout_seconds - passed_seconds) // 60
        return self.timeout


class Punisher:
    """
    Класс для раздачи пиздюлей
    """
    @classmethod
    def set_timeout(cls, driver, timeout: int):
        payload = Payload.get_payload(driver.phone)
        payload.timeout = timeout
        payload.save()

    @classmethod
    def fetch_and_update_busy_drivers_payloads(cls):
        new_busy_payloads = cls._get_new_busy_payloads()

        current_busy_payloads = []
        for payload in new_busy_payloads:
            old_payload = Payload.get_payload(payload.phone)
            if old_payload:
                payload.penalties = old_payload.penalties + 1

            payload.save()
            current_busy_payloads.append(payload)

        return current_busy_payloads

    @staticmethod
    def _get_new_busy_payloads(way='selenium') -> List[Payload]:
        """
        Данные из диспетчерской
        """
        if way == 'selenium':
            with SeleniumClient(YANDEX_LOGIN, YANDEX_PASSWORD) as client:
                drivers = client.get_drivers_from_map()
            return [
                Payload(phone=d['phone'], penalties=1)
                for d in drivers
                if d['status'] == 'Busy' and int(d['minutes']) >= MAX_BUSY_MINUTES
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

import os
from datetime import datetime

from config import PAYLOAD_FN
from fs_store import Store


class Payload:
    """
    Протокол хранения данных о занятых водителях
    """

    def __init__(self, name, surname, penalties: int = 0, timeout: int = None, timeout_set_at: datetime = None):
        self.name = name
        self.surname = surname
        self.penalties = penalties
        self.timeout = timeout
        self.timeout_set_at = timeout_set_at

    def __str__(self):
        return f'{self.name}_{self.surname}'

    def increment_penalties(self):
        self.penalties += 1
        self.save()

    def save(self):
        Store.store_failsafe(self.get_path(self.name, self.surname), self)

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

    @classmethod
    def get_path(cls, name: str, surname: str):
        return PAYLOAD_FN.format(cls._get_fn_format(name, surname))

    @classmethod
    def exists(cls, name: str, surname: str):
        return os.path.exists(cls._get_fn_format(name, surname))

    @classmethod
    def _get_fn_format(cls, name: str, surname: str):
        return f'{name.lower()}{surname.lower()}'

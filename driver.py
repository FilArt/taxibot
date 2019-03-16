import os
from datetime import datetime

from config import DRIVERS_SECRETS_FN, DRIVER_PATH
from fs_store import Store
from log import driver_logger as logger


class DriverStatus:
    def __init__(self, value: str, duracity: int, last_updated_at: datetime = datetime.now()):
        self.value = value
        self.duracity = duracity
        self.last_updated_at = last_updated_at

    @property
    def busy(self):
        return self.value == 'Busy'


class DriverInfo:
    def __init__(self, name, surname, patronymic, phone, status: DriverStatus = None):
        self.name = name
        self.surname = surname
        self.patronymic = patronymic
        self.phone = phone
        self.status = status
        self.tg_id = None
        self.tg_name = None


class UnregisteredDriver(Exception):
    """Driver unregistered - processing unavailable"""


class Driver(DriverInfo):
    def __str__(self):
        return '{} {}'.format(self.name, self.surname)

    @classmethod
    def from_driver_info(cls, driver_info: DriverInfo, tg_name: str = '', tg_id: int = None) -> 'Driver':
        unfilled = cls(
            name=driver_info.name,
            surname=driver_info.surname,
            patronymic=driver_info.patronymic,
            phone=driver_info.phone,
            status=driver_info.status,
        )
        unfilled.add_tg_info(tg_name, tg_id)
        return unfilled

    def add_tg_info(self, tg_name, tg_id):
        self.tg_name = tg_name
        self.tg_id = tg_id

    def save(self):
        if not self.tg_id or not self.tg_name:
            raise UnregisteredDriver("Can't save unregistered driver.")

        path = DRIVER_PATH.format(tg_id=self.tg_id)
        Store.store_failsafe(path, self)
        logger.info(f'driver saved here {path}')

    def to_dict(self):
        return {
            'name': self.name,
            'surname': self.surname,
            'patronymic': self.patronymic,
            'phone': self.phone,
            'tg_name': self.tg_name,
            'tg_id': self.tg_id,
        }

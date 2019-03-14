from collections import namedtuple

import os

from config import DRIVERS_SECRETS_FN, DRIVERS_SYMLINKS
from fs_store import Store
from log import driver_logger as logger

driver_info_factory = namedtuple('driver_info', ('name', 'surname', 'patronymic', 'phone', 'status'))
driver_status_factory = namedtuple('driver_status', ('value', 'duracity', 'last_updated_at'))


class UnregisteredDriver(Exception):
    """Driver unregistered - processing unavailable"""


class Driver:
    def __init__(self, driver_info: driver_info_factory, tg_name: str = '', tg_id: int = None):
        self.name = driver_info.name
        self.surname = driver_info.surname
        self.patronimyc = driver_info.patronymic,
        self.phone = driver_info.phone
        self.tg_name = tg_name
        self.tg_id = tg_id

    def save(self):
        if not self.tg_id or self.tg_name:
            raise UnregisteredDriver("Can't save unregistered driver.")

        path = DRIVERS_SECRETS_FN.format(name=self.name, surname=self.surname)
        Store.store_failsafe(path, self)
        logger.info(f'driver saved here {path}')

        # для удобства будем сохранять еще и симлинк
        # чтобы по tg_id легко достать данные водилы
        symlink_path = self.get_symlink_path(self.tg_id)
        os.symlink(path, symlink_path)
        logger.info(f'symlink to driver saved here {symlink_path}')

    @staticmethod
    def get_symlink_path(tg_id: int):
        return DRIVERS_SYMLINKS.format(tg_id=tg_id)

    def to_dict(self):
        return {
            'name': self.name,
            'surname': self.surname,
            'patronimyc': self.patronimyc,
            'phone': self.phone,
            'tg_name': self.tg_name,
            'tg_id': self.tg_id,
        }

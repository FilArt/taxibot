import os
from collections import namedtuple

from fs_store import Store
from config import DRIVERS_SECRETS_FN, DRIVERS_SYMLINKS
from log import driver_logger as logger


driver_info_factory = namedtuple('driver_info', ('name', 'surname', 'patronymic', 'phone', 'tg_name', 'tg_id'))


class Driver:
    def __init__(self, driver_info: driver_info_factory):
        self.name = driver_info.name
        self.surname = driver_info.surname
        self.phone = driver_info.phone
        self.tg_name = driver_info.tg_name
        self.tg_id = driver_info.tg_id

    def save(self):
        if not self.tg_id:
            raise Exception("Can't save unregistered driver.")

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

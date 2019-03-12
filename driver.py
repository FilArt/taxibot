import os
from fs_store import Store
from config import DRIVERS_SECRETS_FN


class Driver:
    def __init__(self, driver_info: dict):
        self.name = driver_info['name']
        self.surname = driver_info['surname']
        self.telephone = driver_info['telephone']
        self.tg_name = driver_info['tg_name']
        self.tg_id = driver_info['tg_id']

    def save(self):
        path = DRIVERS_SECRETS_FN.format(name=self.name, surname=self.surname)
        Store.store(path, self)

        # для удобства будем сохранять еще и симлинк
        # чтобы по tg_id легко достать данные водилы
        os.symlink(path, DRIVERS_SECRETS_FN.format(tg_id=self.tg_id))

    def to_dict(self):
        return {
            'name': self.name,
            'surname': self.surname,
            'telephone': self.telephone,
            'tg_name': self.tg_name,
            'tg_id': self.tg_id,
        }

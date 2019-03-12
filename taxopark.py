from typing import List

from config import DRIVERS_SECRETS_FN, SECRETS_FN, ALL_DRIVERS_FN
from driver import Driver
from fs_store import Store
from log import taxopark_logger as logger


class InvalidTelephone(Exception):
    """Нет водителя с таким телефоном в локальном хранилище, либо ошибка в формате"""


class Taxopark:
    """
    Локальное хранилище данных водителей (а также их статусов) и админов бота.
    """
    @classmethod
    def register_driver(cls, telephone: str, tg_id: str):
        found = False
        all_drivers = Taxopark.get_all_drivers()
        for i in range(len(all_drivers)):
            if all_drivers[i].telephone == telephone:
                found = True
                all_drivers[i].tg_id = tg_id
                break

        if not found:
            raise InvalidTelephone

        Store.store(ALL_DRIVERS_FN, all_drivers)

    @classmethod
    def get_driver(cls, name: str = '', surname: str = '', tg_id: str = '') -> Driver:
        return Store.load(DRIVERS_SECRETS_FN.format(name=name, surname=surname, tg_id=tg_id))

    @classmethod
    def get_all_drivers(cls) -> List[Driver]:
        return Store.load(ALL_DRIVERS_FN)

    @classmethod
    def get_registered_admins(cls) -> List:
        return cls._get_secret_file().get('admins', [])

    @classmethod
    def get_registered_drivers_tg_ids(cls) -> List:
        return cls._get_secret_file().get('drivers', [])

    @staticmethod
    def _get_secret_file():
        try:
            return Store.load(SECRETS_FN)
        except FileNotFoundError:
            logger.info('creating secrets file')
            Store.store_failsafe(SECRETS_FN, {})

    @classmethod
    def get_registered_drivers(cls) -> List[Driver]:
        return [d for d in Store.load(ALL_DRIVERS_FN) if d.tg_id is not None]

    @classmethod
    def get_unregistered_drivers(cls) -> List[Driver]:
        return [d for d in Store.load(ALL_DRIVERS_FN) if d.tg_id is None]

    @classmethod
    def get_dispatcher_chat_id(cls) -> str:
        # TODO: добавить регистрацию для диспетчеров или захардкодить
        return cls.get_registered_admins()[0]

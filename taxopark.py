import os

from datetime import datetime
from typing import List, Any

from config import DRIVERS_SECRETS_FN, SECRETS_FN, YANDEX_LOGIN, YANDEX_PASSWORD, DRIVERS_SYMLINKS
from driver import Driver, driver_info_factory
from fs_store import Store
from log import taxopark_logger as logger
from payload import Payload
from selenium_client import SeleniumClient


class Taxopark:
    """
    Локальное хранилище данных водителей (а также их статусов) и админов бота.
    """
    drivers_info_list_cache: List[Any] = []
    last_update = datetime.now()

    @classmethod
    def register_driver(cls, driver_index: int, tg_name: str, tg_id: int) -> Driver:
        logger.info(f'registering driver {driver_index}')
        drivers = cls.get_all_drivers_info(refresh=False)
        d_info = drivers[driver_index]
        d_info = driver_info_factory(name=d_info.name, surname=d_info.surname, patronymic=d_info.patronymic,
                                     phone=d_info.phone, status=None)
        driver = Driver(d_info)
        driver.tg_id = tg_id
        driver.tg_name = tg_name
        driver.save()
        return driver

    @classmethod
    def is_registered(cls, name: str, surname: str):
        return os.path.exists(DRIVERS_SECRETS_FN.format(name=name, surname=surname))

    @classmethod
    def get_driver(cls, name: str = '', surname: str = '', tg_id: int = None) -> Driver:
        if not tg_id or (not name and not surname):
            raise Exception("Водитель не зарегистрирован")
        if tg_id:
            return Store.load(DRIVERS_SYMLINKS.format(tg_id=tg_id))
        else:
            return Store.load(DRIVERS_SECRETS_FN.format(name=name, surname=surname))

    @classmethod
    def get_all_drivers_info(cls, refresh=False) -> List[driver_info_factory]:
        if not refresh and cls.drivers_info_list_cache:
            return cls.drivers_info_list_cache

        logger.info('fetching drivers list')
        start = datetime.now()
        with SeleniumClient(YANDEX_LOGIN, YANDEX_PASSWORD) as client:
            drivers_info = client.get_all_drivers_info()
            end = datetime.now()
        elapsed = end - start
        logger.info('drivers list fetched for %i seconds', elapsed.seconds)

        cls.drivers_info_list_cache = drivers_info
        cls.last_update = datetime.now()

        return drivers_info

    @classmethod
    def get_drivers_info_from_map(cls) -> List[Payload]:
        logger.info('fetching drivers from map')
        with SeleniumClient(YANDEX_LOGIN, YANDEX_PASSWORD) as client:
            drivers_info = client.get_drivers_from_map()
        return drivers_info

    @classmethod
    def get_payload(cls, name: str, surname: str) -> Payload:
        return Store.load(Payload.get_path(name, surname))

    @classmethod
    def get_registered_admins(cls) -> List:
        return cls._get_secret_file().get('admins', [])

    @classmethod
    def get_registered_drivers_tg_ids(cls) -> List:
        return cls._get_secret_file().get('drivers', [])

    @classmethod
    def get_dispatcher_chat_id(cls) -> str:
        # TODO: добавить регистрацию для диспетчеров или захардкодить
        return cls.get_registered_admins()[0]

    @staticmethod
    def _get_secret_file():
        try:
            return Store.load(SECRETS_FN)
        except FileNotFoundError:
            logger.info('creating secrets file')
            Store.store_failsafe(SECRETS_FN, {})
            return Store.load(SECRETS_FN)

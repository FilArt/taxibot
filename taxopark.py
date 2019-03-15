import os
from datetime import datetime
from typing import List

from cache import Cache
from config import DRIVERS_SECRETS_FN, SECRETS_FN, DRIVERS_SYMLINKS, DRIVERS_INFO_CACHE
from driver import Driver, DriverInfo
from fs_store import Store
from log import taxopark_logger as logger
from payload import Payload
from selenium_client import SeleniumClient


class Taxopark:
    """
    Локальное хранилище данных водителей (а также их статусов) и админов бота.
    """
    @classmethod
    def register_driver(cls, driver_index: int, tg_name: str, tg_id: int) -> Driver:
        logger.info(f'registering driver {driver_index}')
        drivers = cls.get_all_drivers_info()
        d_info = drivers[driver_index]
        d_info = DriverInfo(name=d_info.name, surname=d_info.surname, patronymic=d_info.patronymic,
                            phone=d_info.phone, status=None)
        driver = Driver.from_driver_info(d_info)
        driver.tg_id = tg_id
        driver.tg_name = tg_name
        driver.save()
        return driver

    @classmethod
    def set_timeout(cls, name: str, surname: str, timeout: int):
        payload = cls.get_payload(name, surname)
        payload.timeout = timeout
        payload.timeout_set_at = datetime.now()
        logger.info('set timeout %i for %s %s', timeout, name, surname)

    @classmethod
    def is_registered(cls, name: str, surname: str, tg_id=None):
        if tg_id:
            return os.path.exists(DRIVERS_SYMLINKS.format(tg_id))
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
    def get_all_drivers(cls, refresh=True) -> List[Driver]:
        drivers = []
        for driver_info in cls.get_all_drivers_info(refresh=refresh):
            name, surname = driver_info.name, driver_info.surname
            if Taxopark.is_registered(name, surname):
                driver = Taxopark.get_driver(name=driver_info.name, surname=driver_info.surname)
            else:
                driver = Driver.from_driver_info(driver_info)
            drivers.append(driver)
        return drivers

    @classmethod
    def get_all_drivers_info(cls, refresh=True) -> List[DriverInfo]:
        logger.info('fetching drivers list')

        if refresh is True:
            Cache.refresh(DRIVERS_INFO_CACHE)

        start = datetime.now()
        drivers_info = SeleniumClient.get_all_drivers_info()
        end = datetime.now()
        elapsed = end - start
        logger.info('drivers list fetched for %i seconds', elapsed.seconds)
        return drivers_info

    @classmethod
    def get_drivers_info_from_map(cls) -> List[DriverInfo]:
        logger.info('fetching drivers from map')
        drivers_info = SeleniumClient.get_drivers_from_map()
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

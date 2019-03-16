from time import sleep

import os
from datetime import datetime
from typing import List

from cache import Cache
from config import DRIVERS_SECRETS_FN, SECRETS_FN, DRIVER_PATH, DRIVERS_INFO_CACHE
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
        logger.info(f'registering driver {tg_name} with id {tg_id}')
        drivers = cls._get_all_drivers_info()
        d_info = drivers[driver_index]
        d_info = DriverInfo(name=d_info.name, surname=d_info.surname, patronymic=d_info.patronymic,
                            phone=d_info.phone, status=None)
        driver = Driver.from_driver_info(d_info)
        driver.add_tg_info(tg_name, tg_id)
        driver.save()
        return driver

    @classmethod
    def set_timeout(cls, name: str, surname: str, timeout: int):
        payload = cls.get_payload(name, surname)
        payload.timeout = timeout
        payload.timeout_set_at = datetime.now()
        payload.save()
        logger.info('set timeout %i for %s %s', timeout, name, surname)

    @classmethod
    def is_registered(cls, tg_id: int = None):
        return os.path.exists(DRIVER_PATH.format(tg_id=tg_id))

    @classmethod
    def get_driver(cls, name: str = '', surname: str = '', tg_id: int = None) -> Driver:
        if not tg_id and (not name and not surname):
            raise Exception("Водитель не зарегистрирован")
        if tg_id:
            return Store.load(DRIVER_PATH.format(tg_id=tg_id))
        else:
            return Store.load(DRIVERS_SECRETS_FN.format(name=name, surname=surname))

    @classmethod
    def get_payload(cls, name: str, surname: str) -> Payload:
        return Payload.load_or_create(name, surname)

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

    @classmethod
    def get_all_drivers(cls, refresh=True) -> List[Driver]:
        logger.info('fetching all drivers')

        if refresh:
            logger.info('cleaning drivers cache')
            Cache.refresh(DRIVERS_INFO_CACHE)

        drivers_info = SeleniumClient.get_all_drivers_info()
        logger.info('all drivers fetched')
        return cls._drivers_info_to_drivers(drivers_info)

    @classmethod
    def get_all_drivers_from_map(cls) -> List[Driver]:
        logger.info('fetching drivers list from map')
        drivers_info = SeleniumClient.get_drivers_info_from_map()
        logger.info('drivers from map fetched')
        return cls._drivers_info_to_drivers(drivers_info)

    @classmethod
    def _drivers_info_to_drivers(cls, drivers_info: List[DriverInfo]) -> List[Driver]:
        drivers = []
        for driver_info in drivers_info:
            if Taxopark.is_registered(driver_info.tg_id):
                driver = Taxopark.get_driver(name=driver_info.name, surname=driver_info.surname)
            else:
                driver = Driver.from_driver_info(driver_info)
            drivers.append(driver)
        return drivers

    @classmethod
    @Cache.cached(DRIVERS_INFO_CACHE, logger=logger)
    def _get_all_drivers_info(cls) -> List[DriverInfo]:
        logger.info('fetching drivers list')
        drivers_info = SeleniumClient.get_all_drivers_info()
        logger.info('fetched all drivers')
        return drivers_info

    @classmethod
    def _get_drivers_info_from_map(cls) -> List[DriverInfo]:
        drivers_info = SeleniumClient.get_drivers_info_from_map()
        return drivers_info

    @staticmethod
    def _get_secret_file():
        try:
            return Store.load(SECRETS_FN)
        except FileNotFoundError:
            logger.info('creating secrets file')
            Store.store_failsafe(SECRETS_FN, {})
            return Store.load(SECRETS_FN)

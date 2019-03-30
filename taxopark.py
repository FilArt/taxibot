from datetime import datetime
from mongoengine import DoesNotExist, MultipleObjectsReturned
from typing import List, Dict, Iterable

from config import DEBUG
from db import Driver, Payload, Admin, Config
from log import taxopark_logger as logger
from selenium_client import SeleniumClient


class Taxopark:
    """
    Локальное хранилище данных водителей (а также их статусов) и админов бота.
    """

    @classmethod
    def is_admin(cls, tg_id: int):
        try:
            Admin.objects.get(tg_id=tg_id)
            return True
        except DoesNotExist:
            return False

    @classmethod
    def is_registered_by_tg_id(cls, tg_id: int):
        try:
            Driver.objects.get(tg__id=tg_id)
            return True
        except DoesNotExist:
            return False
        except MultipleObjectsReturned:
            if DEBUG:
                return True
            raise

    @classmethod
    def get_driver_by_phone(cls, phone: str):
        try:
            return Driver.objects.get(phone=phone)
        except DoesNotExist:
            return None

    @classmethod
    def register_admin(cls, tg_id):
        new_admin = Admin(tg_id=tg_id)
        new_admin.save()

    @classmethod
    def register_driver(cls, driver: Driver, tg_name: str, tg_id: int) -> Driver:
        logger.info(f"registering driver {tg_name} with id {tg_id}")
        driver.add_tg_info(tg_name, tg_id)
        driver.save()
        return driver

    @classmethod
    def add_timeout(cls, driver: Driver, timeout: int):
        payload = cls.get_payload(driver)
        if not payload.timeout:
            payload.timeout_set_at = datetime.now()

        if payload.timeout:
            payload.timeout += timeout
        else:
            payload.timeout = timeout

        payload.save()
        logger.info("add timeout %i for %s %s", timeout, driver.name, driver.surname)

    @classmethod
    def update_tg_name(cls, driver: Driver, tg_name: str):
        driver.tg.name = tg_name
        driver.save()

    @classmethod
    def update_tg_id(cls, driver: Driver, tg_id: int):
        driver.tg.id = tg_id
        driver.save()

    @classmethod
    def is_registered(cls, driver: Driver):
        return driver.tg is not None

    @classmethod
    def get_driver(cls, driver_id: str = None, tg_id: int = None) -> Driver:
        return (
            Driver.objects.get(id=driver_id)
            if driver_id
            else Driver.objects.get(tg__id=tg_id)
        )

    @classmethod
    def get_payload(cls, driver: Driver) -> Payload:
        try:
            return Payload.objects.get(driver=driver)
        except DoesNotExist:
            return Payload(driver=driver, penalty=0)

    @classmethod
    def get_admin(cls) -> Admin:
        return Admin.objects[0]

    @classmethod
    def get_registered_drivers(cls) -> List[Driver]:
        return [d for d in Driver.objects if d.tg is not None]

    @classmethod
    def get_unregistered_drivers(cls) -> List[Driver]:
        all_drivers = SeleniumClient.get_all_drivers_info()
        result = []
        for driver in all_drivers:
            if Driver.objects.filter(**driver):
                continue

            driver = Driver.from_driver_info(driver)
            result.append(driver)
        return result

    @classmethod
    def get_dispatcher_chat_id(cls) -> int:
        conf = Config.get()
        return conf.dispatcher_chat_id

    @classmethod
    def get_all_drivers(cls) -> List[Driver]:
        logger.info("fetching all drivers")
        drivers_info = SeleniumClient.get_all_drivers_info()
        logger.info("all drivers fetched")
        return cls._drivers_info_to_drivers(drivers_info)

    @classmethod
    def get_all_drivers_from_map(cls) -> List[Driver]:
        logger.info("fetching drivers list from map")
        drivers_info = SeleniumClient.get_drivers_info_from_map()
        return cls._drivers_info_to_drivers(drivers_info)

    @classmethod
    def _get_all_drivers_info(cls) -> Iterable[Dict]:
        logger.info("fetching drivers list")
        yield from SeleniumClient.get_all_drivers_info()

    @classmethod
    def _get_drivers_info_from_map(cls) -> Iterable[Dict]:
        yield from SeleniumClient.get_drivers_info_from_map()

    @classmethod
    def _drivers_info_to_drivers(cls, drivers_info: Iterable[Dict]) -> List[Driver]:
        drivers = []
        for driver_info in drivers_info:
            driver = Driver.from_driver_info(driver_info)
            drivers.append(driver)
        return drivers

from unittest import TestCase

from mongoengine import DoesNotExist

from db import Driver, DriverTG
from taxopark import Taxopark


class TestTaxopark(TestCase):
    def setUp(self):
        self.tg = DriverTG(id='123123123', name='@testusername')
        self.registered_driver = Driver(name='Registered', surname='Testov', phone='+79111231231')
        self.registered_driver.save()
        self.driver = Driver(name='Unregistered', surname='Testov', phone='+79111231232')
        self.driver.save()

    def test_get_driver(self):
        for driver in (self.driver, self.registered_driver):
            driver_from_id = Taxopark.get_driver(driver_id=driver.id)
            driver_from_tg = Taxopark.get_driver(tg_id=driver.tg.id)

            self.assertEqual(driver, driver_from_id)
            self.assertEqual(driver, driver_from_tg)

            with self.assertRaises(DoesNotExist):
                Taxopark.get_driver(driver_id=driver.id)
                Taxopark.get_driver(tg_id=0000000000000)

    def test_registration(self):
        Taxopark.register_driver(self.registered_driver, tg_id=self.tg.id, tg_name=self.tg.name)

        self.assertTrue(Taxopark.is_registered(self.registered_driver))
        self.assertTrue(Taxopark.is_registered_by_tg_id(self.registered_driver.tg.id))
        self.assertNotIn(self.registered_driver, Taxopark.get_unregistered_drivers())
        self.assertIn(self.registered_driver, Taxopark.get_registered_drivers())

        self.assertFalse(Taxopark.is_registered(self.driver))
        self.assertIn(self.driver, Taxopark.get_unregistered_drivers())
        self.assertNotIn(self.driver, Taxopark.get_registered_drivers())

    def test_is_admin(self):
        self.assertFalse(Taxopark.is_admin(self.driver.tg.id))

    def tearDown(self):
        self.driver.delete()
        self.registered_driver.delete()

    # def set_timeout(cls, driver: Driver, timeout: int):
    #     payload = cls.get_payload(driver)
    #     payload.timeout = timeout
    #     payload.timeout_set_at = datetime.now()
    #     payload.save()
    #     logger.info('set timeout %i for %s %s', timeout, name, surname)

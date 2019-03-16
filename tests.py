from unittest import TestCase

import os

from fs_store import Store


class TestFSStore(TestCase):
    def setUp(self):
        self.filename1 = 'tests/test'
        self.filename2 = 'tests/more_tests'
        self.data1 = {'data': [1, 2, 3]}
        self.data2 = {'data': [4, 5, 6]}
        Store.store_failsafe(self.filename1, self.data1)
        Store.store_failsafe(self.filename2, self.data2)

    def test_load(self):
        data1 = Store.load(self.filename1)
        data2 = Store.load(self.filename2)

        self.assertEqual(self.data1, data1)
        self.assertTrue(self.data2, data2)

    def tearDown(self):
        os.remove(self.filename1)
        os.remove(self.filename2)
        os.removedirs('/'.join(self.filename1.split('/')[:-1]))

        second_file = '/'.join(self.filename2.split('/'))
        if os.path.exists(second_file):
            os.removedirs('/'.join(self.filename2.split('/')[:-1]))


# class TestTaxopark(TestCase):
#     def setUp(self):
#         self.driver = Driver('testName', 'testSurname', '', '+7911123123')
#         Taxopark.register_driver(driver_index=0, tg_name='@filart', tg_id=339020478)
#
#     def test_is_registered(self):
#         self.assertTrue(Taxopark.is_registered(name=self.driver.name, surname=self.driver.surname))
#         self.assertTrue(Taxopark.is_registered(tg_id=self.driver.tg_id))
#
#
# class TestPunish(TestCase):
#     def setUp(self):
#         self.driver = Driver('testName', 'testSurname', '', '+7911123123')
#         Taxopark.register_driver(driver_index=0, tg_name='@filart', tg_id=339020478)
#
#     def test_punishment(self):
#         punisher = Punisher(bot)

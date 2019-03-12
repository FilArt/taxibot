import os
from unittest import TestCase

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

import os
import pickle


class Store:

    @staticmethod
    def store(filename, data):
        with open(filename, 'wb') as f:
            pickle.dump(data, f)

    @staticmethod
    def store_failsafe(filename, data):
        splitted_name = filename.split('/')
        if len(splitted_name) > 1:
            *dirs, fn = splitted_name
            dirs = '/'.join(dirs)
            if not os.path.exists(dirs):
                os.makedirs(dirs)

        open(filename, 'w').close()

        if os.path.exists(filename):
            Store.store(filename, data)

    @staticmethod
    def load(filename):
        with open(filename, 'rb') as f:
            data_new = pickle.load(f)
        return data_new

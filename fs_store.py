import os
import pickle


class Store:

    @staticmethod
    def store(filename, data):
        with open(filename, 'wb') as f:
            pickle.dump(data, f)

    @staticmethod
    def load(filename):
        with open(filename, 'rb') as f:
            data_new = pickle.load(f)
        return data_new

    @staticmethod
    def loads(filename):
        if os.path.isfile(filename):
            with open(filename) as f:
                return f.read() or ''
        return ''

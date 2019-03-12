import os
from fs_store import Store


def test_store():
    data = {"old": 1}
    new_data = {"new": 2}

    try:
        Store.store("test.json", data)
        Store.store("test.json", new_data)

        assert Store.load("test.json") == {**data, **new_data}
    finally:
        os.remove("test.json")


test_store()

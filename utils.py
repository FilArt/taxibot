import os

from driver import Driver
from taxopark import Taxopark


def is_admin(tg_id):
    return tg_id in Taxopark.get_registered_admins()


def is_driver(tg_id):
    return os.path.exists(Driver.get_symlink_path(tg_id))


def merge_with_pattern(pattern, driver_info):
    for key, value in driver_info.items():
        if key in pattern:
            pattern = pattern.replace('{'+key+'}', str(value))
    return pattern

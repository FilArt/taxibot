from taxopark import Taxopark


def is_admin(tg_id):
    return tg_id in Taxopark.get_registered_drivers_tg_ids()


def is_driver(tg_id):
    return tg_id in Taxopark.get_registered_drivers_tg_ids()


def merge_with_pattern(pattern, driver_info):
    for key, value in driver_info.items():
        if key in pattern:
            pattern = pattern.replace('{'+key+'}', str(value))
    return pattern

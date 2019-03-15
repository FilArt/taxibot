def merge_with_pattern(pattern, driver_info):
    for key, value in driver_info.items():
        if key in pattern:
            pattern = pattern.replace('{'+key+'}', str(value))
    return pattern

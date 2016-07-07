from coreapi.compat import string_types


# Robust dictionary lookups, that always return an item of the correct
# type, using an empty default if an incorrect type exists.
# Useful for liberal parsing of inputs.

def get_string(item, key):
    value = item.get(key)
    if isinstance(value, string_types):
        return value
    return ''


def get_dict(item, key):
    value = item.get(key)
    if isinstance(value, dict):
        return value
    return {}


def get_list(item, key):
    value = item.get(key)
    if isinstance(value, list):
        return value
    return []


def get_bool(item, key):
    value = item.get(key)
    if isinstance(value, bool):
        return value
    return False

from coreapi.compat import string_types
import itypes


# Helper functions to get an expected type from a dictionary.

def _get_string(item, key):
    value = item.get(key)
    return value if isinstance(value, string_types) else ''


def _get_dict(item, key):
    value = item.get(key)
    return value if isinstance(value, dict) else {}


def _get_list(item, key):
    value = item.get(key)
    return value if isinstance(value, list) else []


def _get_bool(item, key, default=False):
    value = item.get(key)
    return value if isinstance(value, bool) else default


# Helper functions to get an expected type from a list.

def get_dicts(item):
    return [value for value in item if isinstance(value, dict)]


class BaseCodec(itypes.Object):
    media_type = None

    def load(self, bytes, base_url=None):
        raise NotImplementedError()  # pragma: nocover

    def dump(self, document, **kwargs):
        raise NotImplementedError()  # pragma: nocover

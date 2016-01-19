from coreapi.compat import string_types
import itypes


# Helper functions to get an expected type from a dictionary,

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


def _mark_as_not_implemented(method):
    # Mark the method as not implemented, for the purposes for determining
    # if a codec supports encoding only, decoding only, or both.
    method.not_implemented = True
    return method


class BaseCodec(itypes.Object):
    media_type = None

    @_mark_as_not_implemented
    def load(self, bytes, base_url=None):
        raise NotImplementedError()  # pragma: nocover

    @_mark_as_not_implemented
    def dump(self, document, **kwargs):
        raise NotImplementedError()  # pragma: nocover

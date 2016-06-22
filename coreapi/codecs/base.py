from coreapi.compat import string_types
from requests.utils import guess_json_utf
import itypes


# Helper functions to get an expected type from a dictionary.

def dereference(lookup_string, struct):
    """
    Dereference a JSON pointer.
    http://tools.ietf.org/html/rfc6901
    """
    keys = lookup_string.strip('#/').split('/')
    node = struct
    for key in keys:
        node = _get_dict(node, key)
    return node


def is_json_pointer(value):
    return isinstance(value, dict) and ('$ref' in value) and (len(value) == 1)


def _get_string(item, key, default=''):
    value = item.get(key)
    return value if isinstance(value, string_types) else default


def _get_dict(item, key, default={}, dereference_using=None):
    value = item.get(key)
    if isinstance(value, dict):
        if dereference_using and is_json_pointer(value):
            return dereference(value['$ref'], dereference_using)
        return value
    return default.copy()


def _get_list(item, key, default=[]):
    value = item.get(key)
    return value if isinstance(value, list) else list(default)


def _get_bool(item, key, default=False):
    value = item.get(key)
    return value if isinstance(value, bool) else default


# Helper functions to get an expected type from a list.

def get_dicts(item, dereference_using=None):
    ret = [value for value in item if isinstance(value, dict)]
    if dereference_using:
        return [
            dereference(value['$ref'], dereference_using) if is_json_pointer(value) else value
            for value in ret
        ]
    return ret


def get_strings(item):
    return [value for value in item if isinstance(value, string_types)]


def get_json_text(content, charset):
    charset = charset or guess_json_utf(content) or 'utf-8'
    return content.decode(charset)


class BaseCodec(itypes.Object):
    media_type = None

    def load(self, content, base_url=None, charset=None):
        raise NotImplementedError()  # pragma: nocover

    def dump(self, document, **kwargs):
        raise NotImplementedError()  # pragma: nocover

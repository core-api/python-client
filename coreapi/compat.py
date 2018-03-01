# coding: utf-8

import base64
import collections
import sys


__all__ = [
    'urlparse', 'string_types',
    'COMPACT_SEPARATORS', 'VERBOSE_SEPARATORS'
]


try:
    # Python 2
    import urlparse
    import cookielib as cookiejar
    import math

    string_types = (basestring,)
    text_type = unicode
    COMPACT_SEPARATORS = (b',', b':')
    VERBOSE_SEPARATORS = (b',', b': ')

    def b64encode(input_string):
        # Provide a consistently-as-unicode interface across 2.x and 3.x
        return base64.b64encode(input_string)

    def isfinite(num):
        if math.isinf(num) or math.isnan(num):
            return False
        return True

except ImportError:
    # Python 3
    import urllib.parse as urlparse
    from io import IOBase
    from http import cookiejar
    from math import isfinite

    string_types = (str,)
    text_type = str
    COMPACT_SEPARATORS = (',', ':')
    VERBOSE_SEPARATORS = (',', ': ')

    def b64encode(input_string):
        # Provide a consistently-as-unicode interface across 2.x and 3.x
        return base64.b64encode(input_string.encode('ascii')).decode('ascii')


try:
    import coreschema
except ImportError:
    # Temporary shim, to support 'coreschema' until it's fully deprecated.
    def coreschema_to_typesys(item):
        return item
else:
    def coreschema_to_typesys(item):
        from coreapi import typesys

        # We were only ever using the type and title/description,
        # so we don't both to include the full set of keyword arguments here.
        if isinstance(item, coreschema.String):
            return typesys.string(title=item.title, description=item.description)
        elif isinstance(item, coreschema.Integer):
            return typesys.integer(title=item.title, description=item.description)
        elif isinstance(item, coreschema.Number):
            return typesys.number(title=item.title, description=item.description)
        elif isinstance(item, coreschema.Boolean):
            return typesys.boolean(title=item.title, description=item.description)
        elif isinstance(item, coreschema.Enum):
            return typesys.enum(title=item.title, description=item.description, enum=item.enum)
        elif isinstance(item, coreschema.Array):
            return typesys.array(title=item.title, description=item.description)
        elif isinstance(item, coreschema.Object):
            return typesys.obj(title=item.title, description=item.description)
        elif isinstance(item, coreschema.Anything):
            return typesys.any(title=item.title, description=item.description)

        return item

def force_bytes(string):
    if isinstance(string, string_types):
        return string.encode('utf-8')
    return string


def force_text(string):
    if not isinstance(string, string_types):
        return string.decode('utf-8')
    return string


if sys.version_info < (3, 6):
    dict_type = collections.OrderedDict
else:
    dict_type = dict


try:
    import click
    console_style = click.style
except ImportError:
    def console_style(text, **kwargs):
        return text


try:
    from tempfile import _TemporaryFileWrapper
except ImportError:
    _TemporaryFileWrapper = None

# coding: utf-8

import base64


__all__ = [
    'urlparse', 'string_types',
    'COMPACT_SEPARATORS', 'VERBOSE_SEPARATORS'
]


try:
    import urlparse

    string_types = (basestring,)
    text_type = unicode
    COMPACT_SEPARATORS = (b',', b':')
    VERBOSE_SEPARATORS = (b',', b': ')

    def is_file(obj):
        return isinstance(obj, file)

    def b64encode(input_string):
        # Provide a consistently-as-unicode interface across 2.x and 3.x
        return base64.b64encode(input_string)

except ImportError:
    import urllib.parse as urlparse
    from io import IOBase

    string_types = (str,)
    text_type = str
    COMPACT_SEPARATORS = (',', ':')
    VERBOSE_SEPARATORS = (',', ': ')

    def is_file(obj):
        return isinstance(obj, IOBase)

    def b64encode(input_string):
        # Provide a consistently-as-unicode interface across 2.x and 3.x
        return base64.b64encode(input_string.encode('ascii')).decode('ascii')


def force_bytes(string):
    if isinstance(string, string_types):
        return string.encode('utf-8')
    return string


try:
    import click
    console_style = click.style
except ImportError:
    def console_style(text, **kwargs):
        return text

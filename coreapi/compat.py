# coding: utf-8

__all__ = [
    'urlparse', 'string_types',
    'COMPACT_SEPARATORS', 'VERBOSE_SEPARATORS'
]


try:
    import urlparse

    string_types = (type(b''), type(u''))
    text_type = unicode
    COMPACT_SEPARATORS = (b',', b':')
    VERBOSE_SEPARATORS = (b',', b': ')

except ImportError:
    import urllib.parse as urlparse

    string_types = (str,)
    text_type = str
    COMPACT_SEPARATORS = (',', ':')
    VERBOSE_SEPARATORS = (',', ': ')


def force_bytes(string):
    if isinstance(string, string_types):
        return string.encode('utf-8')
    return string

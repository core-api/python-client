# coding: utf-8
from __future__ import unicode_literals
from collections import OrderedDict
from coreapi.codecs.html import HTMLCodec
from coreapi.codecs.corejson import CoreJSONCodec
from coreapi.codecs.plaintext import PlainTextCodec
from coreapi.codecs.python import PythonCodec


__all__ = [
    'CoreJSONCodec', 'HTMLCodec', 'PlainTextCodec', 'PythonCodec',
    'negotiate_encoder', 'negotiate_decoder'
]


# Codec negotiation

REGISTERED_CODECS = OrderedDict([
    ('application/vnd.coreapi+json', CoreJSONCodec),
    ('text/html', HTMLCodec)
])


ACCEPT_HEADER = 'application/vnd.coreapi+json, application/json'

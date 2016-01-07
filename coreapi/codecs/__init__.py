# coding: utf-8
from __future__ import unicode_literals
from coreapi.codecs.html import HTMLCodec
from coreapi.codecs.corejson import CoreJSONCodec
from coreapi.codecs.plaintext import PlainTextCodec
from coreapi.codecs.python import PythonCodec


__all__ = [
    'CoreJSONCodec', 'HTMLCodec', 'PlainTextCodec', 'PythonCodec',
    'negotiate_encoder', 'negotiate_decoder'
]


ACCEPT_HEADER = 'application/vnd.coreapi+json, application/json'

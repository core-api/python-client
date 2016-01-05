# coding: utf-8
from __future__ import unicode_literals
from collections import OrderedDict
from coreapi.exceptions import ParseError, NotAcceptable
from coreapi.codecs.html import HTMLCodec
from coreapi.codecs.corejson import JSONCodec
from coreapi.codecs.plaintext import PlainTextCodec
from coreapi.codecs.python import PythonCodec


__all__ = [
    'JSONCodec', 'HTMLCodec', 'PlainTextCodec', 'PythonCodec',
    'negotiate_encoder', 'negotiate_decoder'
]


# Codec negotiation

def negotiate_decoder(content_type=None):
    """
    Given the value of a 'Content-Type' header, return the appropriate
    codec registered to decode the request content.
    """
    if content_type is None:
        return JSONCodec()

    content_type = content_type.split(';')[0].strip().lower()
    try:
        codec_class = REGISTERED_CODECS[content_type]
    except KeyError:
        raise ParseError(
            "Cannot parse unsupported content type '%s'" % content_type
        )

    if not hasattr(codec_class, 'load'):
        raise ParseError(
            "Cannot parse content type '%s'. This implementation only "
            "supports rendering for that content." % content_type
        )

    return codec_class()


def negotiate_encoder(accept=None):
    """
    Given the value of a 'Accept' header, return a two tuple of the appropriate
    content type and codec registered to encode the response content.
    """
    if accept is None:
        key, codec_class = list(REGISTERED_CODECS.items())[0]
        return key, codec_class()

    media_types = set([
        item.split(';')[0].strip().lower()
        for item in accept.split(',')
    ])

    for key, codec_class in REGISTERED_CODECS.items():
        if key in media_types:
            return key, codec_class()

    for key, codec_class in REGISTERED_CODECS.items():
        if key.split('/')[0] + '/*' in media_types:
            return key, codec_class()

    if '*/*' in media_types:
        key, codec_class = list(REGISTERED_CODECS.items())[0]
        return key, codec_class()

    raise NotAcceptable()


REGISTERED_CODECS = OrderedDict([
    ('application/vnd.coreapi+json', JSONCodec),
    ('application/json', JSONCodec),
    ('application/vnd.coreapi+html', HTMLCodec),
    ('text/html', HTMLCodec)
])


ACCEPT_HEADER = 'application/vnd.coreapi+json, application/json'

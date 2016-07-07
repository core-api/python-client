# coding: utf-8
from coreapi.codecs.base import BaseCodec
from coreapi.codecs.corejson import CoreJSONCodec
from coreapi.codecs.coretext import CoreTextCodec
from coreapi.codecs.jsondata import JSONCodec
from coreapi.codecs.python import PythonCodec
from coreapi.codecs.text import TextCodec
from coreapi.exceptions import NotAcceptable, UnsupportedContentType
import itypes


__all__ = [
    'BaseCodec', 'CoreJSONCodec', 'CoreTextCodec',
    'JSONCodec', 'PythonCodec', 'TextCodec'
]

# Default set of decoders for clients to accept.
default_decoders = itypes.List([
    CoreJSONCodec(), JSONCodec(), TextCodec()
])

# Default set of encoders for servers to respond with.
default_encoders = itypes.List([
    CoreJSONCodec()
])


def negotiate_decoder(content_type=None, decoders=None):
    """
    Given the value of a 'Content-Type' header, return the appropriate
    codec registered to decode the request content.
    """
    if decoders is None:
        decoders = default_decoders

    if content_type is None:
        return decoders[0]

    content_type = content_type.split(';')[0].strip().lower()
    main_type = content_type.split('/')[0] + '/*'
    for codec in decoders:
        if (codec.media_type == content_type) or (codec.media_type == main_type):
            return codec

    msg = "Unsupported media in Content-Type header '%s'" % content_type
    raise UnsupportedContentType(msg)


def negotiate_encoder(accept=None, encoders=None):
    """
    Given the value of a 'Accept' header, return a two tuple of the appropriate
    content type and codec registered to encode the response content.
    """
    if encoders is None:
        encoders = default_encoders

    if accept is None:
        return encoders[0]

    acceptable = set([
        item.split(';')[0].strip().lower()
        for item in accept.split(',')
    ])

    for codec in encoders:
        if codec.media_type in acceptable:
            return codec

    for codec in encoders:
        if codec.media_type.split('/')[0] + '/*' in acceptable:
            return codec

    if '*/*' in acceptable:
        return encoders[0]

    msg = "Unsupported media in Accept header '%s'" % accept
    raise NotAcceptable(msg)


def load(bytestring, content_type=None, base_url=None, decoders=None):
    """
    Given a bytestring and an optional content_type, return the
    parsed Document.
    """
    codec = negotiate_decoder(content_type, decoders=decoders)
    return codec.load(bytestring, base_url=base_url)


def dump(document, accept=None, encoders=None, **kwargs):
    """
    Given a document, and an optional accept header, return a two-tuple of
    the selected media type and encoded bytestring.
    """
    codec = negotiate_encoder(accept, encoders=encoders)
    content = codec.dump(document, **kwargs)
    return (codec.media_type, content)

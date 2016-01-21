# coding: utf-8
from coreapi.codecs import BaseCodec, CoreJSONCodec, HALCodec, HTMLCodec, PlainTextCodec, PythonCodec
from coreapi.document import Array, Document, Link, Object, Error, Field
from coreapi.exceptions import ParseError, TransportError, ErrorMessage
from coreapi.history import History
from coreapi.client import Client
from coreapi.transport import BaseTransport, HTTPTransport


__version__ = '1.11.4'
__all__ = [
    'BaseCodec', 'CoreJSONCodec', 'HALCodec', 'HTMLCodec', 'PlainTextCodec', 'PythonCodec',
    'negotiate_encoder', 'negotiate_decoder',
    'Array', 'Document', 'Link', 'Object', 'Error', 'Field',
    'ParseError', 'NotAcceptable', 'TransportError', 'ErrorMessage',
    'BaseTransport', 'HTTPTransport', 'Client', 'History',
    'load', 'dump', 'get', 'get_default_client'
]


_default_client = Client(
    codecs=[CoreJSONCodec(), HALCodec(), HTMLCodec(), PlainTextCodec()],
    transports=[HTTPTransport()]
)


def get_default_client():
    return _default_client


def get_client(credentials=None, headers=None):
    return Client(
        codecs=_default_client.codecs,
        transports=[HTTPTransport(credentials=credentials, headers=headers)]
    )


def negotiate_encoder(accept=None):
    client = _default_client
    return client.negotiate_encoder(accept)


def negotiate_decoder(content_type=None):
    client = _default_client
    return client.negotiate_decoder(content_type)


def get(url):
    client = _default_client
    return client.get(url)


def action(document, keys, params=None, action=None, inplace=None):
    client = _default_client
    return client.action(document, keys, params, action=action, inplace=inplace)


def reload(document):
    client = _default_client
    return client.reload(document)


def load(bytestring, content_type=None):
    client = _default_client
    codec = client.negotiate_decoder(content_type)
    return codec.load(bytestring)


def dump(document, accept=None, **kwargs):
    client = _default_client
    codec = client.negotiate_encoder(accept)
    content = codec.dump(document, **kwargs)
    return codec.media_type, content

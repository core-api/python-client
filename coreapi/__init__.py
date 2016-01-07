# coding: utf-8
from coreapi.codecs import BaseCodec, CoreJSONCodec, HTMLCodec, PlainTextCodec, PythonCodec
from coreapi.document import Array, Document, Link, Object, Error, required
from coreapi.exceptions import ParseError, TransportError, ErrorMessage
from coreapi.sessions import Session
from coreapi.transport import BaseTransport, HTTPTransport


__version__ = '1.2.1'
__all__ = [
    'BaseCodec', 'CoreJSONCodec', 'HTMLCodec', 'PlainTextCodec', 'PythonCodec',
    'negotiate_encoder', 'negotiate_decoder',
    'Array', 'Document', 'Link', 'Object', 'Error', 'required',
    'ParseError', 'NotAcceptable', 'TransportError', 'ErrorMessage',
    'BaseTransport', 'HTTPTransport',
    'load', 'dump', 'get', 'get_default_session'
]


_default_session = Session(
    codecs=[CoreJSONCodec(), HTMLCodec(), PlainTextCodec()],
    transports=[HTTPTransport()]
)


def get_default_session():
    return _default_session


def get_session(credentials):
    return Session(
        codecs=[CoreJSONCodec(), HTMLCodec(), PlainTextCodec()],
        transports=[HTTPTransport(credentials=credentials)]
    )


def negotiate_encoder(accept=None):
    session = _default_session
    return session.negotiate_encoder(accept)


def negotiate_decoder(content_type=None):
    session = _default_session
    return session.negotiate_decoder(content_type)


def get(url):
    session = _default_session
    return session.get(url)


def action(document, keys, **params):
    session = _default_session
    return session.action(document, keys, **params)


def load(bytestring, content_type=None):
    session = _default_session
    codec = session.negotiate_decoder(content_type)
    return codec.load(bytestring)


def dump(document, accept=None, **kwargs):
    session = _default_session
    codec = session.negotiate_encoder(accept)
    content = codec.dump(document, **kwargs)
    return codec.media_type, content

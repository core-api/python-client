# coding: utf-8
from coreapi.codecs import BaseCodec, CoreJSONCodec, HALCodec, HTMLCodec, PlainTextCodec, PythonCodec
from coreapi.document import Array, Document, Link, Object, Error, Field
from coreapi.exceptions import ParseError, TransportError, ErrorMessage
from coreapi.history import History
from coreapi.sessions import Session
from coreapi.transport import BaseTransport, HTTPTransport


__version__ = '1.11.0'
__all__ = [
    'BaseCodec', 'CoreJSONCodec', 'HALCodec', 'HTMLCodec', 'PlainTextCodec', 'PythonCodec',
    'negotiate_encoder', 'negotiate_decoder',
    'Array', 'Document', 'Link', 'Object', 'Error', 'Field',
    'ParseError', 'NotAcceptable', 'TransportError', 'ErrorMessage',
    'BaseTransport', 'HTTPTransport', 'Session', 'History',
    'load', 'dump', 'get', 'get_default_session'
]


_default_session = Session(
    codecs=[CoreJSONCodec(), HALCodec(), HTMLCodec(), PlainTextCodec()],
    transports=[HTTPTransport()]
)


def get_default_session():
    return _default_session


def get_session(credentials=None, headers=None):
    return Session(
        codecs=_default_session.codecs,
        transports=[HTTPTransport(credentials=credentials, headers=headers)]
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


def action(document, keys, params=None, action=None, inplace=None):
    session = _default_session
    return session.action(document, keys, params, action=action, inplace=inplace)


def reload(document):
    session = _default_session
    return session.reload(document)


def load(bytestring, content_type=None):
    session = _default_session
    codec = session.negotiate_decoder(content_type)
    return codec.load(bytestring)


def dump(document, accept=None, **kwargs):
    session = _default_session
    codec = session.negotiate_encoder(accept)
    content = codec.dump(document, **kwargs)
    return codec.media_type, content

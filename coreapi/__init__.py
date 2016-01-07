# coding: utf-8
from coreapi.codecs import CoreJSONCodec, HTMLCodec, PlainTextCodec, PythonCodec
from coreapi.document import Array, Document, Link, Object, Error, required
from coreapi.document import dotted_path_to_list
from coreapi.exceptions import ParseError, TransportError, ErrorMessage
from coreapi.sessions import Session
from coreapi.transport import HTTPTransport


__version__ = '1.1.0'
__all__ = [
    'CoreJSONCodec', 'HTMLCodec', 'PlainTextCodec', 'PythonCodec',
    'negotiate_encoder', 'negotiate_decoder',
    'Array', 'Document', 'Link', 'Object', 'Error', 'required',
    'dotted_path_to_list',
    'ParseError', 'NotAcceptable', 'TransportError', 'ErrorMessage',
    'HTTPTransport',
    'load', 'dump', 'get', 'get_default_session'
]


_default_session = Session(
    codecs=[CoreJSONCodec(), HTMLCodec()],
    transports=[HTTPTransport()]
)


def get_default_session():
    return _default_session


def negotiate_encoder(accept=None):
    session = _default_session
    return session.negotiate_encoder(accept)


def negotiate_decoder(content_type=None):
    session = _default_session
    return session.negotiate_decoder(content_type)


def get(url):
    session = _default_session
    return session.transition(url, 'get')


def load(bytestring, content_type=None):
    session = _default_session
    codec = session.negotiate_decoder(content_type)
    return codec.load(bytestring)


def dump(document, accept=None, **kwargs):
    session = _default_session
    codec = session.negotiate_encoder(accept)
    content = codec.dump(document, **kwargs)
    return codec.media_type, content

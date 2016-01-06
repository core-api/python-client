# coding: utf-8
from coreapi.codecs import CoreJSONCodec, HTMLCodec, PlainTextCodec, PythonCodec
from coreapi.codecs import negotiate_encoder, negotiate_decoder
from coreapi.document import Array, Document, Link, Object, Error, required
from coreapi.document import dotted_path_to_list
from coreapi.exceptions import ParseError, TransportError, ErrorMessage
from coreapi.transport import transition


__version__ = '1.1.0'
__all__ = [
    'CoreJSONCodec', 'HTMLCodec', 'PlainTextCodec', 'PythonCodec',
    'negotiate_encoder', 'negotiate_decoder',
    'Array', 'Document', 'Link', 'Object', 'Error', 'required',
    'dotted_path_to_list',
    'ParseError', 'NotAcceptable', 'TransportError', 'ErrorMessage',
    'HTTPTransport',
    'load', 'dump', 'get'
]


def load(bytestring, content_type=None):
    codec = negotiate_decoder(content_type)
    return codec.load(bytestring)


def dump(document, accept=None, **kwargs):
    codec = negotiate_encoder(accept)
    content = codec.dump(document, **kwargs)
    return codec.media_type, content


def get(url):
    return transition(url, 'follow')

# coding: utf-8
from coreapi.codecs import JSONCodec, HTMLCodec
from coreapi.codecs import negotiate_encoder, negotiate_decoder
from coreapi.document import Array, Document, Link, Object, Error, required
from coreapi.document import remove, replace, deep_remove, deep_replace
from coreapi.exceptions import ParseError, TransportError, ErrorMessage
from coreapi.transport import transition


__version__ = '0.6.0'
__all__ = [
    'JSONCodec', 'HTMLCodec', 'negotiate_encoder', 'negotiate_decoder',
    'Array', 'Document', 'Link', 'Object', 'Error', 'required',
    'remove', 'replace', 'deep_remove', 'deep_replace',
    'ParseError', 'NotAcceptable', 'TransportError', 'ErrorMessage',
    'HTTPTransport',
    'load', 'dump', 'get'
]


def load(bytestring, content_type=None):
    codec = negotiate_decoder(content_type)
    return codec.load(bytestring)


def dump(document, accept=None, verbose=False):
    content_type, codec = negotiate_encoder(accept)
    content = codec.dump(document, verbose=verbose)
    return content_type, content


def get(url):
    return transition(url, 'follow')

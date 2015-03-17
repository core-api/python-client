from coreapi.document import Array, Document, Link, Object
from coreapi.document import remove, replace, deep_remove, deep_replace
from coreapi.codecs import DocJSONCodec
from coreapi.exceptions import DocumentError, ParseError, RequestError
from coreapi.transport import HTTPTransport


__version__ = '0.1'
__all__ = [
    'Array', 'Document', 'Link', 'Object',
    'remove', 'replace', 'deep_remove', 'deep_replace',
    'dumps', 'get', 'loads',
    'DocumentError', 'ParseError', 'RequestError'
]


def loads(bytestring):
    codec = DocJSONCodec()
    return codec.loads(bytestring)


def dumps(document, indent=None):
    codec = DocJSONCodec()
    return codec.dumps(document, indent=indent)


def get(url):
    transport = HTTPTransport()
    return transport.follow(url)

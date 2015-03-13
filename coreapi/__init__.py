from coreapi.document import Document, Link, Object, List
from coreapi.codecs import DocJSONCodec
from coreapi.exceptions import ParseError, RequestError
from coreapi.transport import HTTPTransport


__version__ = '0.1'


def loads(bytestring):
    codec = DocJSONCodec()
    return codec.loads(bytestring)


def dumps(document, indent=None):
    codec = DocJSONCodec()
    return codec.dumps(document, indent=indent)


def get(url):
    transport = HTTPTransport()
    return transport.follow(url)

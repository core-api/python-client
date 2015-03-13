from coreapi.document import Document, Link, Object, List
from coreapi.encoders import DocJSONEncoder
from coreapi.exceptions import ParseError, RequestError
from coreapi.transport import HTTPTransport


def loads(bytestring):
    encoder = DocJSONEncoder()
    return encoder.loads(bytestring)


def dumps(document, indent=None):
    encoder = DocJSONEncoder()
    return encoder.dumps(document, indent=indent)


def get(uri):
    transport = HTTPTransport()
    return transport.follow(uri)

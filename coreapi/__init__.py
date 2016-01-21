# coding: utf-8
from coreapi.client import Client
from coreapi.document import Array, Document, Link, Object, Error, Field
from coreapi.exceptions import ParseError, TransportError, ErrorMessage
from coreapi import codecs, history, transports


__version__ = '1.12.0'
__all__ = [
    'Array', 'Document', 'Link', 'Object', 'Error', 'Field',
    'ParseError', 'NotAcceptable', 'TransportError', 'ErrorMessage',
    'Client',
    'negotiate_encoder', 'negotiate_decoder',
    'get', 'action', 'reload', 'load', 'dump',
    'codecs', 'history', 'transports'
]


def negotiate_encoder(accept=None):
    client = Client()
    return client.negotiate_encoder(accept)


def negotiate_decoder(content_type=None):
    client = Client()
    return client.negotiate_decoder(content_type)


def get(url):
    client = Client()
    return client.get(url)


def action(document, keys, params=None, action=None, inplace=None):
    client = Client()
    return client.action(document, keys, params, action=action, inplace=inplace)


def reload(document):
    client = Client()
    return client.reload(document)


def load(bytestring, content_type=None):
    client = Client()
    return client.load(bytestring, content_type=content_type)


def dump(document, accept=None, **kwargs):
    client = Client()
    return client.dump(document, accept=accept, **kwargs)

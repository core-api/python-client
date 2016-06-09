# coding: utf-8
from coreapi.codecs import dump, load, negotiate_decoder, negotiate_encoder
from coreapi.client import Client
from coreapi.document import Array, Document, Link, Object, Error, Field
from coreapi.exceptions import ParseError, TransportError, ErrorMessage
from coreapi import codecs, history, transports


__version__ = '1.21.0'
__all__ = [
    'Array', 'Document', 'Link', 'Object', 'Error', 'Field',
    'ParseError', 'NotAcceptable', 'TransportError', 'ErrorMessage',
    'Client',
    'load', 'dump', 'negotiate_encoder', 'negotiate_decoder',
    'get', 'action', 'reload',
    'codecs', 'history', 'transports'
]


def get(url):
    client = Client()
    return client.get(url)


def action(document, keys, params=None, action=None, transform=None):
    client = Client()
    return client.action(document, keys, params, action=action, transform=transform)


def reload(document):
    client = Client()
    return client.reload(document)

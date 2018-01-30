# coding: utf-8
from coreapi import auth, codecs, exceptions, transports, utils
from coreapi.client import Client
from coreapi.document import Document, Link, Object, Error, Field


__version__ = '2.3.3'
__all__ = [
    'Document', 'Link', 'Object', 'Error', 'Field',
    'Client',
    'auth', 'codecs', 'exceptions', 'transports', 'utils',
]

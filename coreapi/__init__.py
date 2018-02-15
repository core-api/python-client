# coding: utf-8
from coreapi import auth, codecs, exceptions, transports, typesys, utils
from coreapi.client import Client
from coreapi.document import Document, Link, Object, Error, Field, Array


__version__ = '3.0.0'
__all__ = [
    'Document', 'Link', 'Object', 'Error', 'Field', 'Array',
    'Client',
    'auth', 'codecs', 'exceptions', 'transports', 'typesys', 'utils',
]

# coding: utf-8
from coreapi.compat import urlparse
from coreapi.exceptions import TransportError
from coreapi.transports.base import BaseTransport
from coreapi.transports.http import HTTPTransport
import itypes


__all__ = [
    'BaseTransport', 'HTTPTransport'
]

default_transports = itypes.List([HTTPTransport()])


def determine_transport(url, transports=default_transports):
    """
    Given a URL determine the appropriate transport instance.
    """
    url_components = urlparse.urlparse(url)
    scheme = url_components.scheme.lower()
    netloc = url_components.netloc

    if not scheme:
        raise TransportError("URL missing scheme '%s'." % url)

    if not netloc:
        raise TransportError("URL missing hostname '%s'." % url)

    for transport in transports:
        if scheme in transport.schemes:
            return transport

    raise TransportError("Unsupported URL scheme '%s'." % scheme)

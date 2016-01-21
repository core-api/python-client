# coding: utf-8
from __future__ import unicode_literals


class ParseError(Exception):
    """
    Raised when an invalid Core API encoding is encountered.
    """
    pass


class UnsupportedContentType(Exception):
    """
    Raised when the media specified in the reponse 'Content-Type' header
    is not supported.
    """
    pass


class NotAcceptable(Exception):
    """
    Raised when the client 'Accept' header could not be satisfied.
    """
    pass


class TransportError(Exception):
    """
    Raised when the transport layer fails to make a request or get a response.
    """
    pass


class LinkLookupError(Exception):
    """
    Raised when `.action` fails to index a link in the document.
    """
    pass


class ErrorMessage(Exception):
    """
    Raised when the transition returns an error message.
    """
    def __init__(self, error):
        self.error = error

    def __repr__(self):
        return 'ErrorMessage(%s)' % repr(self.error)

    def __str__(self):
        return str(self.error)

# coding: utf-8


class ParseError(Exception):
    """
    Raised when an invalid Core API encoding is encountered.
    """
    pass


class TransportError(Exception):
    """
    Raised when the transport layer fails to make a request or get a response.
    """
    pass

# coding: utf-8


class LinkError(Exception):
    """
    Raised when an invalid transition occurs, when calling a link.
    """
    pass


class ParseError(Exception):
    """
    Raised when an invalid Core API encoding is encountered.
    """
    pass


class RequestError(Exception):
    """
    Raised when the transport layer fails to make a request or get a response.
    """
    pass

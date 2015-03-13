#coding: utf-8


class DocumentError(Exception):
    pass


class ParseError(Exception):
    """
    Raised when invalid DocJSON content is encountered.
    """
    pass


class RequestError(Exception):
    """
    Raised when the transport layer fails to make a request or get a response.
    """
    pass

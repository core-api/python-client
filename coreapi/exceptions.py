# coding: utf-8
from __future__ import unicode_literals
from coreapi.compat import string_types


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


class ErrorMessage(Exception):
    """
    Raised when the transition returns an error message.
    """
    def __init__(self, messages):
        if not isinstance(messages, (list, tuple)):
            raise TypeError("'messages' should be a list of strings.")
        if any([not isinstance(message, string_types) for message in messages]):
            raise TypeError("'messages' should be a list of strings.")

        self.messages = tuple(messages)

    def __repr__(self):
        return 'ErrorMessage(%s)' % repr(list(self.messages))

    def __str__(self):
        return '<ErrorMessage>' + ''.join([
            '\n    * %s' % repr(message) for message in self.messages
        ])

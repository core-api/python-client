# coding: utf-8
from coreapi import ErrorMessage


def test_error_message_repr():
    error = ErrorMessage(['failed'])
    assert repr(error) == "ErrorMessage(['failed'])"


def test_error_message_str():
    error = ErrorMessage(['failed'])
    assert str(error) == "['failed']"

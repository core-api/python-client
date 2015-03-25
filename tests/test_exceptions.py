# coding: utf-8
from coreapi import ErrorMessage
import pytest


def test_error_messages_must_be_list():
    with pytest.raises(TypeError):
        ErrorMessage(123)


def test_error_messages_must_be_list_of_strings():
    with pytest.raises(TypeError):
        ErrorMessage([123])


def test_error_message_repr():
    error = ErrorMessage(['failed'])
    assert repr(error) == "ErrorMessage(['failed'])"


def test_error_message_str():
    error = ErrorMessage(['failed'])
    assert str(error) == "<ErrorMessage>\n    * 'failed'"

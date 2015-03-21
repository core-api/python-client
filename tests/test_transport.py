# coding: utf-8
from coreapi.exceptions import RequestError
from coreapi.transport import transition
import pytest


def test_unknown_scheme():
    with pytest.raises(RequestError):
        transition('ftp://example.org')


def test_missing_hostname():
    with pytest.raises(RequestError):
        transition('http://')

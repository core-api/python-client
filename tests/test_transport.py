# coding: utf-8
from coreapi.exceptions import TransportError
from coreapi.transport import transition
import pytest


def test_unknown_scheme():
    with pytest.raises(TransportError):
        transition('ftp://example.org')


def test_missing_hostname():
    with pytest.raises(TransportError):
        transition('http://')

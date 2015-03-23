# coding: utf-8
from coreapi.exceptions import TransportError
from coreapi.transport import transition, HTTPTransport
import pytest
import requests


@pytest.fixture
def http():
    return HTTPTransport()


class MockResponse(object):
    def __init__(self, content):
        self.content = content
        self.headers = {}


# Test transport errors.

def test_unknown_scheme():
    with pytest.raises(TransportError):
        transition('ftp://example.org')


def test_missing_scheme():
    with pytest.raises(TransportError):
        transition('example.org')


def test_missing_hostname():
    with pytest.raises(TransportError):
        transition('http://')


# Test basic transition types.

def test_follow(monkeypatch, http):
    def mockreturn(method, url):
        return MockResponse(b'{"_type": "document", "example": 123}')

    monkeypatch.setattr(requests, 'request', mockreturn)

    doc = http.transition(
        url='http://example.org',
        trans='follow'
    )
    assert doc == {'example': 123}


def test_follow_with_parameters(monkeypatch, http):
    def mockreturn(method, url, params):
        return MockResponse(
            b'{"_type": "document", "example": "' +
            params['example'].encode('utf-8') +
            b'"}'
        )

    monkeypatch.setattr(requests, 'request', mockreturn)

    doc = http.transition(
        url='http://example.org',
        trans='follow',
        parameters={'example': 'abc'}
    )
    assert doc == {'example': 'abc'}


def test_create(monkeypatch, http):
    def mockreturn(method, url, data, headers):
        return MockResponse(
            b'{"_type": "document", "data": ' + data + b'}'
        )

    monkeypatch.setattr(requests, 'request', mockreturn)

    doc = http.transition(
        url='http://example.org',
        trans='action',
        parameters={'example': 'abc'}
    )
    assert doc == {'data': {'example': 'abc'}}


def test_delete(monkeypatch, http):
    def mockreturn(method, url):
        return MockResponse(b'')

    monkeypatch.setattr(requests, 'request', mockreturn)

    doc = http.transition(
        url='http://example.org',
        trans='delete'
    )
    assert doc is None

# coding: utf-8
from coreapi.exceptions import TransportError
from coreapi.sessions import DefaultSession
from coreapi.transport import HTTPTransport
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
    session = DefaultSession()
    with pytest.raises(TransportError):
        session.transition('ftp://example.org')


def test_missing_scheme():
    session = DefaultSession()
    with pytest.raises(TransportError):
        session.transition('example.org')


def test_missing_hostname():
    session = DefaultSession()
    with pytest.raises(TransportError):
        session.transition('http://')


# Test basic transition types.

def test_get(monkeypatch, http):
    def mockreturn(method, url, headers):
        return MockResponse(b'{"_type": "document", "example": 123}')

    monkeypatch.setattr(requests, 'request', mockreturn)

    doc = http.transition(
        url='http://example.org',
        action='get'
    )
    assert doc == {'example': 123}


def test_get_with_parameters(monkeypatch, http):
    def mockreturn(method, url, params, headers):
        insert = params['example'].encode('utf-8')
        return MockResponse(
            b'{"_type": "document", "example": "' + insert + b'"}'
        )

    monkeypatch.setattr(requests, 'request', mockreturn)

    doc = http.transition(
        url='http://example.org',
        action='get',
        parameters={'example': 'abc'}
    )
    assert doc == {'example': 'abc'}


def test_post(monkeypatch, http):
    def mockreturn(method, url, data, headers):
        insert = data.encode('utf-8')
        return MockResponse(b'{"_type": "document", "data": ' + insert + b'}')

    monkeypatch.setattr(requests, 'request', mockreturn)

    doc = http.transition(
        url='http://example.org',
        action='post',
        parameters={'example': 'abc'}
    )
    assert doc == {'data': {'example': 'abc'}}


def test_delete(monkeypatch, http):
    def mockreturn(method, url, headers):
        return MockResponse(b'')

    monkeypatch.setattr(requests, 'request', mockreturn)

    doc = http.transition(
        url='http://example.org',
        action='delete'
    )
    assert doc is None

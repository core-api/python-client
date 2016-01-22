# coding: utf-8
from coreapi import Link, Field
from coreapi.exceptions import TransportError
from coreapi.transports import determine_transport, HTTPTransport
import pytest
import requests


@pytest.fixture
def http():
    return HTTPTransport()


class MockResponse(object):
    def __init__(self, content):
        self.content = content
        self.headers = {}
        self.url = 'http://example.org'
        self.status_code = 200


# Test transport errors.

def test_unknown_scheme():
    with pytest.raises(TransportError):
        determine_transport('ftp://example.org')


def test_missing_scheme():
    with pytest.raises(TransportError):
        determine_transport('example.org')


def test_missing_hostname():
    with pytest.raises(TransportError):
        determine_transport('http://')


# Test basic transition types.

def test_get(monkeypatch, http):
    def mockreturn(method, url, **opts):
        return MockResponse(b'{"_type": "document", "example": 123}')

    monkeypatch.setattr(requests, 'request', mockreturn)

    link = Link(url='http://example.org', action='get')
    doc = http.transition(link)
    assert doc == {'example': 123}


def test_get_with_parameters(monkeypatch, http):
    def mockreturn(method, url, **opts):
        insert = opts['params']['example'].encode('utf-8')
        return MockResponse(
            b'{"_type": "document", "example": "' + insert + b'"}'
        )

    monkeypatch.setattr(requests, 'request', mockreturn)

    link = Link(url='http://example.org', action='get')
    doc = http.transition(link, params={'example': 'abc'})
    assert doc == {'example': 'abc'}


def test_get_with_path_parameter(monkeypatch, http):
    def mockreturn(method, url, **opts):
        insert = url.encode('utf-8')
        return MockResponse(
            b'{"_type": "document", "example": "' + insert + b'"}'
        )

    monkeypatch.setattr(requests, 'request', mockreturn)

    link = Link(
        url='http://example.org/{user_id}/',
        action='get',
        fields=[Field(name='user_id', location='path')]
    )
    doc = http.transition(link, params={'user_id': 123})
    assert doc == {'example': 'http://example.org/123/'}


def test_post(monkeypatch, http):
    def mockreturn(method, url, **opts):
        insert = opts['data'].encode('utf-8')
        return MockResponse(b'{"_type": "document", "data": ' + insert + b'}')

    monkeypatch.setattr(requests, 'request', mockreturn)

    link = Link(url='http://example.org', action='post')
    doc = http.transition(link, params={'example': 'abc'})
    assert doc == {'data': {'example': 'abc'}}


def test_delete(monkeypatch, http):
    def mockreturn(method, url, **opts):
        return MockResponse(b'')

    monkeypatch.setattr(requests, 'request', mockreturn)

    link = Link(url='http://example.org', action='delete')
    doc = http.transition(link)
    assert doc.url == 'http://example.org'
    assert not doc.items()
    assert not doc.title


# Test credentials

def test_credentials(monkeypatch):
    credentials = {'example.org': 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=='}
    transport = HTTPTransport(credentials=credentials)

    # Requests to example.org include credentials.
    headers = transport.get_headers('http://example.org/123')
    assert 'authorization' in headers
    assert headers['authorization'] == 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=='

    # Requests to other.org do not include credentials.
    headers = transport.get_headers('http://other.org/123')
    assert 'authorization' not in headers


# Test custom headers

def test_headers(monkeypatch):
    headers = {'User-Agent': 'Example v1.0'}
    transport = HTTPTransport(headers=headers)

    # Requests include custom headers.
    headers = transport.get_headers('http://example.org/123')
    assert 'user-agent' in headers
    assert headers['user-agent'] == 'Example v1.0'

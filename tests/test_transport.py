# coding: utf-8
from coreapi import get_client, get_default_client, Link, Field
from coreapi.exceptions import TransportError
from coreapi.transports import HTTPTransport
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
    client = get_default_client()
    with pytest.raises(TransportError):
        client.determine_transport('ftp://example.org')


def test_missing_scheme():
    client = get_default_client()
    with pytest.raises(TransportError):
        client.determine_transport('example.org')


def test_missing_hostname():
    client = get_default_client()
    with pytest.raises(TransportError):
        client.determine_transport('http://')


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
    def mockreturn(method, url, **opts):
        return MockResponse(opts['headers'].get('authorization', ''))

    monkeypatch.setattr(requests, 'request', mockreturn)

    credentials = {'example.org': 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=='}
    client = get_client(credentials=credentials)
    transport = client.transports[0]

    # Requests to example.org include credentials.
    response = transport.make_http_request(client, 'http://example.org/123', 'GET')
    assert response.content == 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=='

    # Requests to other.org do not include credentials.
    response = transport.make_http_request(client, 'http://other.org/123', 'GET')
    assert response.content == ''


# Test custom headers

def test_headers(monkeypatch):
    def mockreturn(method, url, **opts):
        return MockResponse(headers.get('User-Agent', ''))

    monkeypatch.setattr(requests, 'request', mockreturn)

    headers = {'User-Agent': 'Example v1.0'}
    client = get_client(headers=headers)
    transport = client.transports[0]

    # Requests include custom headers.
    response = transport.make_http_request(client, 'http://example.org/123', 'GET')
    assert response.content == 'Example v1.0'

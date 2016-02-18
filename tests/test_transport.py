# coding: utf-8
from coreapi import Document, Link, Field
from coreapi.codecs import CoreJSONCodec
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
        codec = CoreJSONCodec()
        content = codec.dump(Document(content={'data': opts['json']}))
        return MockResponse(content)

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
    assert doc is None

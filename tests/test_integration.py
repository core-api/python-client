# coding: utf-8
from coreapi import get_session, action, get, load, dump, Link, ErrorMessage
import requests
import pytest


encoded = (
    b'{"_type":"document","_meta":{"url":"http://example.org"},'
    b'"a":123,"next":{"_type":"link"}}'
)


@pytest.fixture
def document():
    return load(encoded)


class MockResponse(object):
    def __init__(self, content):
        self.content = content
        self.headers = {}
        self.url = 'http://example.org'


# Basic integration tests.

def test_load():
    assert load(encoded) == {
        "a": 123,
        "next": Link(url='http://example.org')
    }


def test_dump(document):
    content_type, content = dump(document)
    assert content_type == 'application/vnd.coreapi+json'
    assert content == encoded


def test_get(monkeypatch):
    def mockreturn(method, url, headers):
        return MockResponse(b'{"_type": "document", "example": 123}')

    monkeypatch.setattr(requests, 'request', mockreturn)

    doc = get('http://example.org')
    assert doc == {'example': 123}


def test_follow(monkeypatch, document):
    def mockreturn(method, url, headers):
        return MockResponse(b'{"_type": "document", "example": 123}')

    monkeypatch.setattr(requests, 'request', mockreturn)

    doc = action(document, ['next'])
    assert doc == {'example': 123}


def test_error(monkeypatch, document):
    def mockreturn(method, url, headers):
        return MockResponse(b'{"_type": "error", "message": ["failed"]}')

    monkeypatch.setattr(requests, 'request', mockreturn)

    with pytest.raises(ErrorMessage):
        action(document, ['next'])


def test_get_session():
    session = get_session(credentials={'example.org': 'abc'})
    assert len(session.transports) == 1
    assert session.transports[0].credentials == {'example.org': 'abc'}

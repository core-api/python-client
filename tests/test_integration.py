# coding: utf-8
from coreapi import get, load, dump, Link
import requests
import pytest


@pytest.fixture
def document():
    return load(bytestring())


@pytest.fixture
def bytestring():
    return (
        b'{"_type":"document","_meta":{"url":"http://example.org"},'
        b'"a":123,"next":{"_type":"link"}}'
    )


class MockResponse(object):
    def __init__(self, text):
        self.text = text
        self.headers = {}


# Basic integration tests.

def test_load(bytestring):
    assert load(bytestring) == {
        "a": 123,
        "next": Link(url='http://example.org')
    }


def test_dump(document):
    assert dump(document) == bytestring()


def test_get(monkeypatch):
    def mockreturn(method, url):
        return MockResponse('{"_type": "document", "example": 123}')

    monkeypatch.setattr(requests, 'request', mockreturn)

    doc = get('http://example.org')
    assert doc == {'example': 123}


def test_follow(monkeypatch, document):
    def mockreturn(method, url):
        return MockResponse('{"_type": "document", "example": 123}')

    monkeypatch.setattr(requests, 'request', mockreturn)

    doc = document.action(['next'])
    assert doc == {'example': 123}

# coding: utf-8
from coreapi import Document, Link, Client
from coreapi.transports import HTTPTransport
import pytest


class MockTransport(HTTPTransport):
    schemes = ['mock']

    def transition(self, link, decoders, params=None):
        return {'action': link.action, 'params': params}


client = Client(transports=[MockTransport()])


@pytest.fixture
def doc():
    return Document(title='original', content={
        'nested': Document(content={
            'follow': Link(url='mock://example.com', action='get'),
            'create': Link(url='mock://example.com', action='post', fields=['foo']),
            'update': Link(url='mock://example.com', action='put', fields=['foo']),
            'delete': Link(url='mock://example.com', action='delete')
        })
    })


# Test valid transitions.

def test_get(doc):
    data = client.action(doc, ['nested', 'follow'])
    assert data == {'action': 'get', 'params': {}}


def test_post(doc):
    data = client.action(doc, ['nested', 'create'], params={'foo': 456})
    assert data == {'action': 'post', 'params': {'foo': 456}}


def test_put(doc):
    data = client.action(doc, ['nested', 'update'], params={'foo': 789})
    assert data == {'action': 'put', 'params': {'foo': 789}}


def test_delete(doc):
    data = client.action(doc, ['nested', 'delete'])
    assert data == {'action': 'delete', 'params': {}}


# Test overrides

def test_override_action(doc):
    data = client.action(doc, ['nested', 'follow'], overrides={'action': 'put'})
    assert data == {'action': 'put', 'params': {}}

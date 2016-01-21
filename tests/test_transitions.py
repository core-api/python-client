# coding: utf-8
from coreapi import Document, Link, Client
from coreapi.transports import HTTPTransport
import pytest


class MockTransport(HTTPTransport):
    schemes = ['mock']

    def transition(self, link, params=None, client=None, link_ancestors=None):
        if link.action == 'get':
            document = Document(title='new', content={'new': 123})
        elif link.action in ('put', 'post'):
            document = Document(title='new', content={'new': 123, 'foo': params.get('foo')})
        else:
            document = None

        return self.handle_inplace_replacements(document, link, link_ancestors)


client = Client(codecs=[], transports=[MockTransport()])


@pytest.fixture
def doc():
    return Document(title='original', content={
        'nested': Document(content={
            'follow': Link(url='mock://example.com', action='get'),
            'action': Link(url='mock://example.com', action='post', inplace=True, fields=['foo']),
            'create': Link(url='mock://example.com', action='post', fields=['foo']),
            'update': Link(url='mock://example.com', action='put', fields=['foo']),
            'delete': Link(url='mock://example.com', action='delete')
        })
    })


# Test valid transitions.

def test_get(doc):
    new = client.action(doc, ['nested', 'follow'])
    assert new == {'new': 123}
    assert new.title == 'new'


def test_inline_post(doc):
    new = client.action(doc, ['nested', 'action'], params={'foo': 123})
    assert new == {'nested': {'new': 123, 'foo': 123}}
    assert new.title == 'original'


def test_post(doc):
    new = client.action(doc, ['nested', 'create'], params={'foo': 456})
    assert new == {'new': 123, 'foo': 456}
    assert new.title == 'new'


def test_put(doc):
    new = client.action(doc, ['nested', 'update'], params={'foo': 789})
    assert new == {'nested': {'new': 123, 'foo': 789}}
    assert new.title == 'original'


def test_delete(doc):
    new = client.action(doc, ['nested', 'delete'])
    assert new == {}
    assert new.title == 'original'


# Test overrides

def test_override_action(doc):
    new = client.action(doc, ['nested', 'follow'], action='put')
    assert new == {'nested': {'new': 123, 'foo': None}}
    assert new.title == 'original'


def test_override_inplace(doc):
    new = client.action(doc, ['nested', 'update'], params={'foo': 456}, inplace=False)
    assert new == {'new': 123, 'foo': 456}
    assert new.title == 'new'

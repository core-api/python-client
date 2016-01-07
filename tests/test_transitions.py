# coding: utf-8
from coreapi import action, Document, Link, BaseTransport, Session
import datetime
import pytest


class MockTransport(BaseTransport):
    schemes = ['mock']

    def transition(self, url, action=None, params=None):
        if action == 'get':
            return Document(title='new', content={'new': 123})
        elif action in ('put', 'post'):
            return Document(title='new', content={'new': 123, 'param': params.get('param')})
        return None


now = datetime.datetime.now()
session = Session(codecs=[], transports=[MockTransport()])


@pytest.fixture
def doc():
    return Document(title='original', content={
        'nested': Document(content={
            'follow': Link(url='mock://example.com', action='get'),
            'action': Link(url='mock://example.com', action='post', transition='inline', fields=['param']),
            'create': Link(url='mock://example.com', action='post', fields=['param']),
            'update': Link(url='mock://example.com', action='put', fields=['param']),
            'delete': Link(url='mock://example.com', action='delete')
        })
    })


# Test valid transitions.

def test_get(doc):
    new = session.action(doc, ['nested', 'follow'])
    assert new == {'new': 123}
    assert new.title == 'new'


def test_inline_post(doc):
    new = session.action(doc, ['nested', 'action'], param=123)
    assert new == {'nested': {'new': 123, 'param': 123}}
    assert new.title == 'original'


def test_post(doc):
    new = session.action(doc, ['nested', 'create'], param=456)
    assert new == {'new': 123, 'param': 456}
    assert new.title == 'new'


def test_put(doc):
    new = session.action(doc, ['nested', 'update'], param=789)
    assert new == {'nested': {'new': 123, 'param': 789}}
    assert new.title == 'original'


def test_delete(doc):
    new = session.action(doc, ['nested', 'delete'])
    assert new == {}
    assert new.title == 'original'


# Test invalid parameters.

def test_invalid_type(doc):
    with pytest.raises(TypeError):
        action(doc, ['nested', 'update'], param=now)


def test_invalid_type_in_list(doc):
    with pytest.raises(TypeError):
        action(doc, ['nested', 'update'], param=[now])


def test_invalid_type_in_dict(doc):
    with pytest.raises(TypeError):
        action(doc, ['nested', 'update'], param=[{"a": now}])


def test_invalid_key_in_dict(doc):
    with pytest.raises(TypeError):
        action(doc, ['nested', 'update'], param=[{1: "a"}])

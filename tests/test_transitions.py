# coding: utf-8
from coreapi import Document, Link
import datetime
import pytest


now = datetime.datetime.now()


# Transition functions.

def follow(document, link):
    return Document(title='new', content={'new': 123})


def action(document, link, **parameters):
    return Document(title='new', content={'new': 123, 'param': parameters.get('param')})


def create(document, link, **parameters):
    return Document(title='new', content={'new': 123, 'param': parameters.get('param')})


def update(document, link, **parameters):
    return Document(title='new', content={'new': 123, 'param': parameters.get('param')})


def delete(document, link, **parameters):
    return None


@pytest.fixture
def doc():
    return Document(title='original', content={
        'nested': Document(content={
            'follow': Link(trans='follow', func=follow),
            'action': Link(trans='action', fields=['param'], func=action),
            'create': Link(trans='create', fields=['param'], func=create),
            'update': Link(trans='update', fields=['param'], func=update),
            'delete': Link(trans='delete', func=delete)
        })
    })


# Test valid transitions.

def test_follow(doc):
    new = doc.action(['nested', 'follow'])
    assert new == {'new': 123}
    assert new.title == 'new'


def test_action(doc):
    new = doc.action(['nested', 'action'], param=123)
    assert new == {'nested': {'new': 123, 'param': 123}}
    assert new.title == 'original'


def test_create(doc):
    new = doc.action(['nested', 'create'], param=456)
    assert new == {'new': 123, 'param': 456}
    assert new.title == 'new'


def test_update(doc):
    new = doc.action(['nested', 'update'], param=789)
    assert new == {'nested': {'new': 123, 'param': 789}}
    assert new.title == 'original'


def test_delete(doc):
    new = doc.action(['nested', 'delete'])
    assert new == {}
    assert new.title == 'original'


# Test invalid parameters.

def test_invalid_type(doc):
    with pytest.raises(TypeError):
        doc.action(['nested', 'update'], param=now)


def test_invalid_type_in_list(doc):
    with pytest.raises(TypeError):
        doc.action(['nested', 'update'], param=[now])


def test_invalid_type_in_dict(doc):
    with pytest.raises(TypeError):
        doc.action(['nested', 'update'], param=[{"a": now}])


def test_invalid_key_in_dict(doc):
    with pytest.raises(TypeError):
        doc.action(['nested', 'update'], param=[{1: "a"}])

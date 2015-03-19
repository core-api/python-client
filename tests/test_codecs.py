from coreapi import Document, Link
from coreapi.codecs import _document_to_primative, _primative_to_document
import pytest


@pytest.fixture
def doc():
    return Document({
        'meta': {
            'url': 'http://example.org',
            'title': 'Example'
        },
        'integer': 123,
        'dict': {'key': 'value'},
        'list': [1, 2, 3],
        'link': Link(url='/'),
        'nested': {'child': Link(url='/123')},
        '_type': 'needs escaping'
    })


def test_document_to_primative(doc):
    data = _document_to_primative(doc)
    assert data == {
        '_type': 'document',
        'meta': {
            'url': 'http://example.org',
            'title': 'Example'
        },
        'integer': 123,
        'dict': {'key': 'value'},
        'list': [1, 2, 3],
        'link': {'_type': 'link', 'url': '/'},
        'nested': {'child': {'_type': 'link', 'url': '/123'}},
        '__type': 'needs escaping'
    }


def test_primative_to_document(doc):
    data = {
        '_type': 'document',
        'meta': {
            'url': 'http://example.org',
            'title': 'Example'
        },
        'integer': 123,
        'dict': {'key': 'value'},
        'list': [1, 2, 3],
        'link': {'_type': 'link', 'url': '/'},
        'nested': {'child': {'_type': 'link', 'url': '/123'}},
        '__type': 'needs escaping'
    }
    assert _primative_to_document(data) == doc

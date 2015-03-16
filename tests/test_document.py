from coreapi import Array, Document, Object
from coreapi.exceptions import DocumentError
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
        'list': [1, 2, 3]
    })


def test_document_does_not_support_key_assignment(doc):
    with pytest.raises(TypeError):
        doc['integer'] = 456


def test_document_does_not_support_key_deletion(doc):
    with pytest.raises(TypeError):
        del doc['integer']


def test_document_dictionaries_coerced_to_objects(doc):
    assert isinstance(doc['dict'], Object)


def test_document_lists_coerced_to_arrays(doc):
    assert isinstance(doc['list'], Array)


def test_document_repr(doc):
    assert repr(doc) == (
        "Document({'meta': {'title': 'Example', 'url': 'http://example.org'}, "
        "'dict': {'key': 'value'}, 'integer': 123, 'list': [1, 2, 3]})"
    )


def test_document_does_not_support_property_assignement(doc):
    with pytest.raises(TypeError):
        doc.example = 456


def test_document_keys_must_be_strings():
    with pytest.raises(DocumentError):
        Document({'meta': {'url': '', 'title': ''}, 0: 123})


def test_document_values_must_be_valid_primatives():
    with pytest.raises(DocumentError):
        Document({'meta': {'url': '', 'title': ''}, 'a': set()})

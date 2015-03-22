# coding: utf-8
from coreapi import Document, Link, JSONCodec, ParseError, required
from coreapi.codecs import _document_to_primative, _primative_to_document
from coreapi.codecs import _get_registered_codec
import pytest


@pytest.fixture
def json_codec():
    return JSONCodec()


@pytest.fixture
def doc():
    return Document(
        url='http://example.org/',
        title='Example',
        content={
            'integer': 123,
            'dict': {'key': 'value'},
            'list': [1, 2, 3],
            'link': Link(url='http://example.org/'),
            'nested': {'child': Link(url='http://example.org/123')},
            '_type': 'needs escaping'
        })


# Documents have a mapping to python primatives in JSON style.

def test_document_to_primative(doc):
    data = _document_to_primative(doc)
    assert data == {
        '_type': 'document',
        '_meta': {
            'url': 'http://example.org/',
            'title': 'Example'
        },
        'integer': 123,
        'dict': {'key': 'value'},
        'list': [1, 2, 3],
        'link': {'_type': 'link'},
        'nested': {'child': {'_type': 'link', 'url': '/123'}},
        '__type': 'needs escaping'
    }


def test_primative_to_document(doc):
    data = {
        '_type': 'document',
        '_meta': {
            'url': 'http://example.org/',
            'title': 'Example'
        },
        'integer': 123,
        'dict': {'key': 'value'},
        'list': [1, 2, 3],
        'link': {'_type': 'link', 'url': 'http://example.org/'},
        'nested': {'child': {'_type': 'link', 'url': 'http://example.org/123'}},
        '__type': 'needs escaping'
    }
    assert _primative_to_document(data) == doc


# Codecs can load a document successfully.

def test_minimal_document(json_codec):
    """
    Ensure we can load the smallest possible valid JSON encoding.
    """
    doc = json_codec.load('{"_type":"document"}')
    assert isinstance(doc, Document)
    assert doc.url == ''
    assert doc.title == ''
    assert doc == {}


# Parse errors should be raised for invalid encodings.

def test_malformed_json(json_codec):
    """
    Invalid JSON should raise a ParseError.
    """
    with pytest.raises(ParseError):
        json_codec.load('_')


def test_not_a_document(json_codec):
    """
    Valid JSON that does not return a document as the top level element
    should raise a ParseError.
    """
    with pytest.raises(ParseError):
        json_codec.load('{}')


# Encodings may have a verbose and a compact style.

def test_compact_style(json_codec):
    doc = Document(content={'a': 123, 'b': 456})
    bytes = json_codec.dump(doc)
    assert bytes == b'{"_type":"document","a":123,"b":456}'


def test_verbose_style(json_codec):
    doc = Document(content={'a': 123, 'b': 456})
    bytes = json_codec.dump(doc, verbose=True)
    assert bytes == b"""{
    "_type": "document",
    "a": 123,
    "b": 456
}"""


# Links should use compact format for optional fields, verbose for required.

def test_link_encodings(json_codec):
    doc = Document(content={
        'link': Link(
            trans='action',
            fields=['optional', required('required')]
        )
    })
    bytes = json_codec.dump(doc, verbose=True)
    assert bytes == b"""{
    "_type": "document",
    "link": {
        "_type": "link",
        "trans": "action",
        "fields": [
            "optional",
            {
                "name": "required",
                "required": true
            }
        ]
    }
}"""


# Tests for graceful ommissions.

def test_invalid_document_meta_ignored(json_codec):
    doc = json_codec.load('{"_type": "document", "_meta": 1, "a": 1}')
    assert doc == Document(content={"a": 1})


def test_invalid_document_url_ignored(json_codec):
    doc = json_codec.load('{"_type": "document", "_meta": {"url": 1}, "a": 1}')
    assert doc == Document(content={"a": 1})


def test_invalid_document_title_ignored(json_codec):
    doc = json_codec.load('{"_type": "document", "_meta": {"title": 1}, "a": 1}')
    assert doc == Document(content={"a": 1})


def test_invalid_link_url_ignored(json_codec):
    doc = json_codec.load('{"_type": "document", "link": {"_type": "link", "url": 1}}')
    assert doc == Document(content={"link": Link()})


def test_invalid_link_fields_ignored(json_codec):
    doc = json_codec.load('{"_type": "document", "link": {"_type": "link", "fields": 1}}')
    assert doc == Document(content={"link": Link()})


# Tests for content type lookup.

def test_get_default_content_type():
    assert _get_registered_codec() == JSONCodec


def test_get_supported_content_type():
    assert _get_registered_codec('application/json') == JSONCodec


def test_get_supported_content_type_with_parameters():
    assert _get_registered_codec('application/json; verison=1.0') == JSONCodec


def test_get_unsupported_content_type():
    with pytest.raises(ParseError):
        _get_registered_codec('application/csv')

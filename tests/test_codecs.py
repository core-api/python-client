# coding: utf-8
from coreapi.codecs import CoreJSONCodec
from coreapi.codecs.corejson import _document_to_primitive, _primitive_to_document
from coreapi.document import Document, Link, Error, Field
from coreapi.exceptions import ParseError, NoCodecAvailable
from coreapi.utils import negotiate_decoder, negotiate_encoder
from coreschema import Enum, String
import pytest


@pytest.fixture
def json_codec():
    return CoreJSONCodec()


@pytest.fixture
def doc():
    return Document(
        url='http://example.org/',
        title='Example',
        content={
            'integer': 123,
            'dict': {'key': 'value'},
            'list': [1, 2, 3],
            'link': Link(
                url='http://example.org/',
                fields=[
                    Field(name='noschema'),
                    Field(name='string_example', schema=String()),
                    Field(name='enum_example', schema=Enum(['a', 'b', 'c'])),
                ]),
            'nested': {'child': Link(url='http://example.org/123')},
            '_type': 'needs escaping'
        })


# Documents have a mapping to python primitives in JSON style.

def test_document_to_primitive(doc):
    data = _document_to_primitive(doc)
    assert data == {
        '_type': 'document',
        '_meta': {
            'url': 'http://example.org/',
            'title': 'Example'
        },
        'integer': 123,
        'dict': {'key': 'value'},
        'list': [1, 2, 3],
        'link': {'_type': 'link', 'fields': [
            {'name': 'noschema'},
            {
                'name': 'string_example',
                'schema': {
                    '_type': 'string',
                    'title': '',
                    'description': '',
                },
            },
            {
                'name': 'enum_example',
                'schema': {
                    '_type': 'enum',
                    'title': '',
                    'description': '',
                    'enum': ['a', 'b', 'c'],
                },
            },
        ]},
        'nested': {'child': {'_type': 'link', 'url': '/123'}},
        '__type': 'needs escaping'
    }


def test_primitive_to_document(doc):
    data = {
        '_type': 'document',
        '_meta': {
            'url': 'http://example.org/',
            'title': 'Example'
        },
        'integer': 123,
        'dict': {'key': 'value'},
        'list': [1, 2, 3],
        'link': {
            '_type': 'link',
            'url': 'http://example.org/',
            'fields': [
                {'name': 'noschema'},
                {
                    'name': 'string_example',
                    'schema': {
                        '_type': 'string',
                        'title': '',
                        'description': '',
                    },
                },
                {
                    'name': 'enum_example',
                    'schema': {
                        '_type': 'enum',
                        'title': '',
                        'description': '',
                        'enum': ['a', 'b', 'c'],
                    },
                },
            ],
        },
        'nested': {'child': {'_type': 'link', 'url': 'http://example.org/123'}},
        '__type': 'needs escaping'
    }
    assert _primitive_to_document(data) == doc


def test_error_to_primitive():
    error = Error(title='Failure', content={'messages': ['failed']})
    data = {
        '_type': 'error',
        '_meta': {'title': 'Failure'},
        'messages': ['failed']
    }
    assert _document_to_primitive(error) == data


def test_primitive_to_error():
    error = Error(title='Failure', content={'messages': ['failed']})
    data = {
        '_type': 'error',
        '_meta': {'title': 'Failure'},
        'messages': ['failed']
    }
    assert _primitive_to_document(data) == error


# Codecs can load a document successfully.

def test_minimal_document(json_codec):
    """
    Ensure we can load the smallest possible valid JSON encoding.
    """
    doc = json_codec.decode(b'{"_type":"document"}')
    assert isinstance(doc, Document)
    assert doc.url == ''
    assert doc.title == ''
    assert doc == {}


def test_minimal_error(json_codec):
    """
    Ensure we can load a minimal error message encoding.
    """
    error = json_codec.decode(b'{"_type":"error","_meta":{"title":"Failure"},"messages":["failed"]}')
    assert error == Error(title="Failure", content={'messages': ['failed']})


# Parse errors should be raised for invalid encodings.

def test_malformed_json(json_codec):
    """
    Invalid JSON should raise a ParseError.
    """
    with pytest.raises(ParseError):
        json_codec.decode(b'_')


def test_not_a_document(json_codec):
    """
    Valid JSON that does not return a document should be coerced into one.
    """
    assert json_codec.decode(b'{}') == Document()


# Encodings may have a verbose and a compact style.

def test_compact_style(json_codec):
    doc = Document(content={'a': 123, 'b': 456})
    bytes = json_codec.encode(doc)
    assert bytes == b'{"_type":"document","a":123,"b":456}'


def test_verbose_style(json_codec):
    doc = Document(content={'a': 123, 'b': 456})
    bytes = json_codec.encode(doc, indent=True)
    assert bytes == b"""{
    "_type": "document",
    "a": 123,
    "b": 456
}"""


# Links should use compact format for optional fields, verbose for required.

def test_link_encodings(json_codec):
    doc = Document(content={
        'link': Link(
            action='post',
            transform='inplace',
            fields=['optional', Field('required', required=True, location='path')]
        )
    })
    bytes = json_codec.encode(doc, indent=True)
    assert bytes == b"""{
    "_type": "document",
    "link": {
        "_type": "link",
        "action": "post",
        "transform": "inplace",
        "fields": [
            {
                "name": "optional"
            },
            {
                "name": "required",
                "required": true,
                "location": "path"
            }
        ]
    }
}"""


# Tests for graceful omissions.

def test_invalid_document_meta_ignored(json_codec):
    doc = json_codec.decode(b'{"_type": "document", "_meta": 1, "a": 1}')
    assert doc == Document(content={"a": 1})


def test_invalid_document_url_ignored(json_codec):
    doc = json_codec.decode(b'{"_type": "document", "_meta": {"url": 1}, "a": 1}')
    assert doc == Document(content={"a": 1})


def test_invalid_document_title_ignored(json_codec):
    doc = json_codec.decode(b'{"_type": "document", "_meta": {"title": 1}, "a": 1}')
    assert doc == Document(content={"a": 1})


def test_invalid_link_url_ignored(json_codec):
    doc = json_codec.decode(b'{"_type": "document", "link": {"_type": "link", "url": 1}}')
    assert doc == Document(content={"link": Link()})


def test_invalid_link_fields_ignored(json_codec):
    doc = json_codec.decode(b'{"_type": "document", "link": {"_type": "link", "fields": 1}}')
    assert doc == Document(content={"link": Link()})


# Tests for 'Content-Type' header lookup.

def test_get_default_decoder():
    codec = negotiate_decoder([CoreJSONCodec()])
    assert isinstance(codec, CoreJSONCodec)


def test_get_supported_decoder():
    codec = negotiate_decoder([CoreJSONCodec()], 'application/vnd.coreapi+json')
    assert isinstance(codec, CoreJSONCodec)


def test_get_supported_decoder_with_parameters():
    codec = negotiate_decoder([CoreJSONCodec()], 'application/vnd.coreapi+json; verison=1.0')
    assert isinstance(codec, CoreJSONCodec)


def test_get_unsupported_decoder():
    with pytest.raises(NoCodecAvailable):
        negotiate_decoder([CoreJSONCodec()], 'application/csv')


# Tests for 'Accept' header lookup.

def test_get_default_encoder():
    codec = negotiate_encoder([CoreJSONCodec()])
    assert isinstance(codec, CoreJSONCodec)


def test_encoder_preference():
    codec = negotiate_encoder(
        [CoreJSONCodec()],
        accept='text/html; q=1.0, application/vnd.coreapi+json; q=1.0'
    )
    assert isinstance(codec, CoreJSONCodec)


def test_get_accepted_encoder():
    codec = negotiate_encoder(
        [CoreJSONCodec()],
        accept='application/vnd.coreapi+json'
    )
    assert isinstance(codec, CoreJSONCodec)


def test_get_underspecified_encoder():
    codec = negotiate_encoder(
        [CoreJSONCodec()],
        accept='application/*'
    )
    assert isinstance(codec, CoreJSONCodec)


def test_get_unsupported_encoder():
    with pytest.raises(NoCodecAvailable):
        negotiate_encoder([CoreJSONCodec()], 'application/csv')


def test_get_unsupported_encoder_with_fallback():
    codec = negotiate_encoder([CoreJSONCodec()], accept='application/csv, */*')
    assert isinstance(codec, CoreJSONCodec)

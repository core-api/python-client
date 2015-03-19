# coding: utf-8
from collections import OrderedDict
from coreapi.compat import string_types
from coreapi.document import Document, Link, Array, Object
from coreapi.exceptions import ParseError
import json


def _escape_type(string):
    """
    The '_type' is reserved, so escape to '__type' if it occurs.
    """
    if string.startswith('_') and string.lstrip('_') == 'type':
        return '_' + string
    return string


def _unescape_type(string):
    """
    Unescape '__type' if it occurs.
    """
    if string.startswith('__') and string.lstrip('_') == 'type':
        return string[1:]
    return string


def _document_to_primative(node):
    """
    Take a Core API document and return Python primatives
    ready to be rendered into the JSON style encoding.
    """
    if isinstance(node, Document):
        ret = OrderedDict()
        ret['_type'] = 'document'
        ret.update([
            (_escape_type(key), _document_to_primative(value))
            for key, value in node.items()
        ])
        return ret

    elif isinstance(node, Link):
        ret = OrderedDict()
        ret['_type'] = 'link'
        ret['url'] = node.url
        if node.rel:
            ret['rel'] = node.rel
        if node.fields:
            ret['fields'] = node.fields
        return ret

    elif isinstance(node, Object):
        return OrderedDict([
            (_escape_type(key), _document_to_primative(value))
            for key, value in node.items()
        ])

    elif isinstance(node, Array):
        return [_document_to_primative(value) for value in node]

    return node


def _primative_to_document(data):
    """
    Take Python primatives as returned from parsing JSON content,
    and return a Core API document.
    """
    if isinstance(data, dict) and data.get('_type') == 'document':
        if 'meta' not in data:
            raise ParseError("Document missing 'meta' section.")
        if not isinstance(data['meta'], dict):
            raise ParseError("Document 'meta' section must be an object.")
        if 'url' not in data['meta']:
            raise ParseError("Document missing 'meta.url' section.")
        if not isinstance(data['meta']['url'], string_types):
            raise ParseError("Document 'meta.url' must be a string.")

        # Note that we ignore anything in 'meta' except url and title.
        # All other keys are reserved.
        url = data['meta']['url']
        title = str(data['meta'].get('title', ''))

        items = [
            ('meta', {'url': url, 'title': title})
        ] + [
            (key, value) for key, value in data.items()
            if key != '_type' and key != 'meta'
        ]

        return Document({
            _unescape_type(key): _primative_to_document(value)
            for key, value in items
        })

    elif isinstance(data, dict) and data.get('_type') == 'link':
        if 'url' not in data:
            raise ParseError("Link missing 'url'.")
        if not isinstance(data['url'], string_types):
            raise ParseError("Link 'url' must be a string.")

        url = data['url']
        rel = data.get('rel')
        fields = data.get('fields', [])
        return Link(
            url=url,
            rel=rel,
            fields=fields
        )

    elif isinstance(data, dict):
        return Object({
            _unescape_type(key): _primative_to_document(value)
            for key, value in data.items()
            if key != '_type'
        })

    elif isinstance(data, list):
        return Array([
            _primative_to_document(item) for item in data
        ])

    return data


class JSONCodec(object):
    media_type = 'TODO'

    def loads(self, bytes, base_url=None):
        """
        Takes a bytestring and returns a document.
        """
        try:
            data = json.loads(bytes)
        except ValueError as exc:
            raise ParseError('Malformed JSON. ' + str(exc))

        doc = _primative_to_document(data)
        if not isinstance(doc, Document):
            raise ParseError('Top level node must be a document.')

        return doc

    def dumps(self, document, indent=None):
        """
        Takes a document and returns a bytestring.
        """
        data = _document_to_primative(document)
        return json.dumps(data, indent=indent)

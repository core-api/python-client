# coding: utf-8
from __future__ import unicode_literals
from collections import OrderedDict
from coreapi.compat import string_types, force_bytes, urlparse
from coreapi.compat import COMPACT_SEPARATORS, VERBOSE_SEPARATORS
from coreapi.document import Document, Link, Array, Object, Error, Field
from coreapi.document import _transition_types, _default_transition_type
from coreapi.document import _graceful_relative_url
from coreapi.exceptions import ParseError
import json


def _escape_key(string):
    """
    The '_type' and '_meta' keys are reserved.
    Prefix with an additional '_' if they occur.
    """
    if string.startswith('_') and string.lstrip('_') in ('type', 'meta'):
        return '_' + string
    return string


def _unescape_key(string):
    """
    Unescape '__type' and '__meta' keys if they occur.
    """
    if string.startswith('__') and string.lstrip('_') in ('type', 'meta'):
        return string[1:]
    return string


def _document_to_primative(node, base_url=None):
    """
    Take a Core API document and return Python primatives
    ready to be rendered into the JSON style encoding.
    """
    if isinstance(node, Document):
        ret = OrderedDict()
        ret['_type'] = 'document'

        # Only fill in items in '_meta' if required.
        meta = OrderedDict()
        url = _graceful_relative_url(base_url, node.url)
        if url:
            meta['url'] = url
        if node.title:
            meta['title'] = node.title
        if meta:
            ret['_meta'] = meta

        ret.update([
            (_escape_key(key), _document_to_primative(value, base_url=node.url))
            for key, value in node.items()
        ])
        return ret

    elif isinstance(node, Link):
        ret = OrderedDict()
        ret['_type'] = 'link'
        url = _graceful_relative_url(base_url, node.url)
        if url:
            ret['url'] = url
        if node.trans != _default_transition_type:
            ret['trans'] = node.trans
        if node.fields:
            # Use short format for optional fields, long format for required.
            ret['fields'] = [
                item.name
                if not item.required else
                OrderedDict([('name', item.name), ('required', item.required)])
                for item in node.fields
            ]
        return ret

    elif isinstance(node, Object):
        return OrderedDict([
            (_escape_key(key), _document_to_primative(value, base_url=base_url))
            for key, value in node.items()
        ])

    elif isinstance(node, Array):
        return [_document_to_primative(value) for value in node]

    elif isinstance(node, Error):
        ret = OrderedDict()
        ret['_type'] = 'error'
        ret['messages'] = node.messages
        return ret

    return node


def _primative_to_document(data, base_url=None):
    """
    Take Python primatives as returned from parsing JSON content,
    and return a Core API document.
    """
    if isinstance(data, dict) and data.get('_type') == 'document':
        meta = data.get('_meta', {})
        if not isinstance(meta, dict):
            meta = {}

        url = meta.get('url', '')
        if not isinstance(url, string_types):
            url = ''
        url = urlparse.urljoin(base_url, url)

        title = meta.get('title', '')
        if not isinstance(title, string_types):
            title = ''

        return Document(url=url, title=title, content={
            _unescape_key(key): _primative_to_document(value, url)
            for key, value in data.items()
            if key not in ('_type', '_meta')
        })

    elif isinstance(data, dict) and data.get('_type') == 'link':
        url = data.get('url', '')
        if not isinstance(url, string_types):
            url = ''
        url = urlparse.urljoin(base_url, url)

        trans = data.get('trans')
        if not isinstance(trans, string_types) or (trans not in _transition_types):
            trans = None

        fields = data.get('fields', [])
        if not isinstance(fields, list):
            fields = []
        else:
            # Ignore any field items that don't match the required structure.
            fields = [
                item for item in fields
                if isinstance(item, string_types) or (
                    isinstance(item, dict) and
                    isinstance(item.get('name'), string_types)
                )
            ]
            # Transform the strings or dicts into strings or Field instances.
            fields = [
                item if isinstance(item, string_types) else
                Field(item['name'], required=bool(item.get('required', False)))
                for item in fields
            ]

        return Link(url=url, trans=trans, fields=fields)

    elif isinstance(data, dict) and data.get('_type') == 'error':
        messages = data.get('messages', [])
        if not isinstance(messages, list):
            messages = []

        # Ignore any messages which are have incorrect type.
        messages = [
            message for message in messages
            if isinstance(message, string_types)
        ]

        return Error(messages)

    elif isinstance(data, dict):
        return Object({
            _unescape_key(key): _primative_to_document(value, base_url)
            for key, value in data.items()
            if key not in ('_type', '_meta')
        })

    elif isinstance(data, list):
        return Array([
            _primative_to_document(item, base_url) for item in data
        ])

    return data


def _get_registered_codec(content_type=None):
    """
    Given the value of a 'Content-Type' header, return the appropriate
    codec registered to handle it.
    """
    if content_type is None:
        return JSONCodec

    content_type = content_type.split(';')[0].strip().lower()
    try:
        return REGISTERED_CODECS[content_type]
    except KeyError:
        raise ParseError(
            "Cannot parse unsupported content type '%s'" % content_type
        )


class JSONCodec(object):
    def load(self, bytes, base_url=None):
        """
        Takes a bytestring and returns a document.
        """
        try:
            data = json.loads(bytes.decode('utf-8'))
        except ValueError as exc:
            raise ParseError('Malformed JSON. %s' % exc)

        doc = _primative_to_document(data, base_url)
        if not isinstance(doc, (Document, Error)):
            raise ParseError('Top level node must be a document or error message.')

        return doc

    def dump(self, document, verbose=False):
        """
        Takes a document and returns a bytestring.
        """
        if verbose:
            options = {
                'ensure_ascii': False,
                'indent': 4,
                'separators': VERBOSE_SEPARATORS
            }
        else:
            options = {
                'ensure_ascii': False,
                'indent': None,
                'separators': COMPACT_SEPARATORS
            }

        data = _document_to_primative(document)
        return force_bytes(json.dumps(data, **options))


REGISTERED_CODECS = {
    'application/vnd.coreapi+json': JSONCodec,
    'application/json': JSONCodec
}

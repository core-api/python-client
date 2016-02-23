from __future__ import unicode_literals
from collections import OrderedDict
from coreapi.codecs.base import BaseCodec, _get_string, _get_dict, _get_list, _get_bool
from coreapi.compat import force_bytes, urlparse
from coreapi.compat import COMPACT_SEPARATORS, VERBOSE_SEPARATORS
from coreapi.document import Document, Link, Array, Object, Error, Field
from coreapi.exceptions import ParseError
import json


def _graceful_relative_url(base_url, url):
    """
    Return a graceful link for a URL relative to a base URL.

    * If they are the same, return an empty string.
    * If the have the same scheme and hostname, return the path & query params.
    * Otherwise return the full URL.
    """
    if url == base_url:
        return ''
    base_prefix = '%s://%s' % urlparse.urlparse(base_url or '')[0:2]
    url_prefix = '%s://%s' % urlparse.urlparse(url or '')[0:2]
    if base_prefix == url_prefix and url_prefix != '://':
        return url[len(url_prefix):]
    return url


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


def _get_content(item, base_url=None):
    """
    Return a dictionary of content, for documents, objects and errors.
    """
    return {
        _unescape_key(key): _primative_to_document(value, base_url)
        for key, value in item.items()
        if key not in ('_type', '_meta')
    }


def _document_to_primative(node, base_url=None):
    """
    Take a Core API document and return Python primatives
    ready to be rendered into the JSON style encoding.
    """
    if isinstance(node, Document):
        ret = OrderedDict()
        ret['_type'] = 'document'

        meta = OrderedDict()
        url = _graceful_relative_url(base_url, node.url)
        if url:
            meta['url'] = url
        if node.title:
            meta['title'] = node.title
        if meta:
            ret['_meta'] = meta

        # Fill in key-value content.
        ret.update([
            (_escape_key(key), _document_to_primative(value, base_url=url))
            for key, value in node.items()
        ])
        return ret

    elif isinstance(node, Error):
        ret = OrderedDict()
        ret['_type'] = 'error'

        if node.title:
            ret['_meta'] = {'title': node.title}

        # Fill in key-value content.
        ret.update([
            (_escape_key(key), _document_to_primative(value, base_url=base_url))
            for key, value in node.items()
        ])
        return ret

    elif isinstance(node, Link):
        ret = OrderedDict()
        ret['_type'] = 'link'
        url = _graceful_relative_url(base_url, node.url)
        if url:
            ret['url'] = url
        if node.action:
            ret['action'] = node.action
        if node.encoding:
            ret['encoding'] = node.encoding
        if node.transform:
            ret['transform'] = node.transform
        if node.description:
            ret['description'] = node.description
        if node.fields:
            ret['fields'] = [
                _document_to_primative(field) for field in node.fields
            ]
        return ret

    elif isinstance(node, Field):
        ret = OrderedDict({'name': node.name})
        if node.required:
            ret['required'] = node.required
        if node.location:
            ret['location'] = node.location
        if node.description:
            ret['description'] = node.description
        return ret

    elif isinstance(node, Object):
        return OrderedDict([
            (_escape_key(key), _document_to_primative(value, base_url=base_url))
            for key, value in node.items()
        ])

    elif isinstance(node, Array):
        return [_document_to_primative(value) for value in node]

    return node


def _primative_to_document(data, base_url=None):
    """
    Take Python primatives as returned from parsing JSON content,
    and return a Core API document.
    """
    if isinstance(data, dict) and data.get('_type') == 'document':
        # Document
        meta = _get_dict(data, '_meta')
        url = _get_string(meta, 'url')
        url = urlparse.urljoin(base_url, url)
        title = _get_string(meta, 'title')
        content = _get_content(data, base_url=url)
        return Document(url=url, title=title, content=content)

    if isinstance(data, dict) and data.get('_type') == 'error':
        # Error
        meta = _get_dict(data, '_meta')
        title = _get_string(meta, 'title')
        content = _get_content(data, base_url=base_url)
        return Error(title=title, content=content)

    elif isinstance(data, dict) and data.get('_type') == 'link':
        # Link
        url = _get_string(data, 'url')
        url = urlparse.urljoin(base_url, url)
        action = _get_string(data, 'action')
        encoding = _get_string(data, 'encoding')
        transform = _get_string(data, 'transform')
        description = _get_string(data, 'description')
        fields = _get_list(data, 'fields')
        fields = [
            Field(
                name=_get_string(item, 'name'),
                required=_get_bool(item, 'required'),
                location=_get_string(item, 'location'),
                description=_get_string(item, 'description')
            )
            for item in fields if isinstance(item, dict)
        ]
        return Link(
            url=url, action=action, encoding=encoding, transform=transform,
            description=description, fields=fields
        )

    elif isinstance(data, dict):
        # Map
        content = _get_content(data, base_url=base_url)
        return Object(content)

    elif isinstance(data, list):
        # Array
        content = [_primative_to_document(item, base_url) for item in data]
        return Array(content)

    # String, Integer, Number, Boolean, null.
    return data


class CoreJSONCodec(BaseCodec):
    media_type = 'application/vnd.coreapi+json'

    def load(self, bytes, base_url=None):
        """
        Takes a bytestring and returns a document.
        """
        try:
            data = json.loads(bytes.decode('utf-8'))
        except ValueError as exc:
            raise ParseError('Malformed JSON. %s' % exc)

        doc = _primative_to_document(data, base_url)

        if isinstance(doc, Object):
            doc = Document(content=dict(doc))
        elif not (isinstance(doc, Document) or isinstance(doc, Error)):
            raise ParseError('Top level node should be a document or error.')

        return doc

    def dump(self, document, indent=False, **kwargs):
        """
        Takes a document and returns a bytestring.
        """
        if indent:
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

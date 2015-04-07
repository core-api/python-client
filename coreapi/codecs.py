# coding: utf-8
from __future__ import unicode_literals
from collections import OrderedDict
from coreapi.compat import string_types, force_bytes, urlparse
from coreapi.compat import COMPACT_SEPARATORS, VERBOSE_SEPARATORS
from coreapi.document import Document, Link, Array, Object, Error, Field
from coreapi.document import _transition_types, _default_transition_type
from coreapi.document import _graceful_relative_url
from coreapi.exceptions import ParseError, NotAcceptable
import jinja2
import json


# JSON encoding

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


# HTML encoding

env = jinja2.Environment(loader=jinja2.PackageLoader('coreapi', 'templates'))


def _render_html(node, url=None, key=None):
    if isinstance(node, (Document, Link)):
        url = urlparse.urljoin(url, node.url)

    if isinstance(node, Document):
        template = env.get_template('document.html')
    elif isinstance(node, Object):
        template = env.get_template('object.html')
    elif isinstance(node, Array):
        template = env.get_template('array.html')
    elif isinstance(node, Link):
        template = env.get_template('link.html')
    elif isinstance(node, Error):
        template = env.get_template('error.html')
    elif node in (True, False, None):
        value = {True: 'true', False: 'false', None: 'null'}[node]
        return "<code>%s</code>" % value
    elif isinstance(node, (float, int)):
        return "<code>%s</code>" % node
    else:
        return "<span>%s</span>" % node

    return template.render(node=node, render=_render_html, url=url, key=key)


class HTMLCodec(object):
    def dump(self, document, verbose=None):
        template = env.get_template('index.html')
        return template.render(document=document, render=_render_html)


# Codec negotiation

def negotiate_decoder(content_type=None):
    """
    Given the value of a 'Content-Type' header, return the appropriate
    codec registered to decode the request content.
    """
    if content_type is None:
        return JSONCodec()

    content_type = content_type.split(';')[0].strip().lower()
    try:
        codec_class = REGISTERED_CODECS[content_type]
    except KeyError:
        raise ParseError(
            "Cannot parse unsupported content type '%s'" % content_type
        )

    if not hasattr(codec_class, 'load'):
        raise ParseError(
            "Cannot parse content type '%s'. This implementation only "
            "supports rendering for that content." % content_type
        )

    return codec_class()


def negotiate_encoder(accept=None):
    """
    Given the value of a 'Accept' header, return a two tuple of the appropriate
    content type and codec registered to encode the response content.
    """
    if accept is None:
        key, codec_class = list(REGISTERED_CODECS.items())[0]
        return key, codec_class()

    media_types = set([
        item.split(';')[0].strip().lower()
        for item in accept.split(',')
    ])

    for key, codec_class in REGISTERED_CODECS.items():
        if key in media_types:
            return key, codec_class()

    for key, codec_class in REGISTERED_CODECS.items():
        if key.split('/')[0] + '/*' in media_types:
            return key, codec_class()

    if '*/*' in media_types:
        key, codec_class = list(REGISTERED_CODECS.items())[0]
        return key, codec_class()

    raise NotAcceptable()


REGISTERED_CODECS = OrderedDict([
    ('application/vnd.coreapi+json', JSONCodec),
    ('application/json', JSONCodec),
    ('application/vnd.coreapi+html', HTMLCodec),
    ('text/html', HTMLCodec)
])


ACCEPT_HEADER = 'application/vnd.coreapi+json, application/json'

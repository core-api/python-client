from collections import OrderedDict
from coreapi.codecs.base import BaseCodec
from coreapi.compat import force_bytes, urlparse
from coreapi.compat import COMPACT_SEPARATORS, VERBOSE_SEPARATORS
from coreapi.document import Document, Link, Array, Object
import json


def _graceful_relative_url(base_url, url):
    """
    Return a graceful link for a URL relative to a base URL.

    * If the have the same scheme and hostname, return the path & query params.
    * Otherwise return the full URL.
    """
    if not url:
        return base_url or '/'
    base_prefix = '%s://%s' % urlparse.urlparse(base_url or '')[0:2]
    url_prefix = '%s://%s' % urlparse.urlparse(url or '')[0:2]
    if base_prefix == url_prefix and url_prefix != '://':
        return url[len(url_prefix):]
    return url


def _is_array_containing_instance(value, datatype):
    return isinstance(value, Array) and value and isinstance(value[0], datatype)


def _document_to_primative(node, base_url=None):
    if isinstance(node, Document):
        url = _graceful_relative_url(base_url, node.url)
        links = OrderedDict()
        embedded = OrderedDict()
        data = OrderedDict()

        self_link = OrderedDict()
        self_link['href'] = url
        if node.title:
            self_link['title'] = node.title
        links['self'] = self_link

        for key, value in node.items():
            if isinstance(value, Link):
                links[key] = _document_to_primative(value, base_url=url)
            elif _is_array_containing_instance(value, Link):
                links[key] = [
                    _document_to_primative(item, base_url=url)
                    for item in value
                    if isinstance(value, Link)
                ]
            elif isinstance(value, Document):
                embedded[key] = _document_to_primative(value, base_url=url)
            elif _is_array_containing_instance(value, Document):
                embedded[key] = [
                    _document_to_primative(item, base_url=url)
                    for item in value
                    if isinstance(item, Document)
                ]
            elif key not in ('_links', '_embedded'):
                data[key] = _document_to_primative(value)

        ret = OrderedDict()
        ret['_links'] = links
        ret.update(data)
        ret['_embedded'] = embedded
        return ret

    elif isinstance(node, Link):
        ret = OrderedDict()
        ret['href'] = _graceful_relative_url(node.url, base_url)
        if node.fields and node.action.lower() in ('get', ''):
            ret['href'] += "{?%s}" % ','.join([field.name for field in node.fields])
            ret['templated'] = True
        return ret

    elif isinstance(node, Array):
        return [
            _document_to_primative(item) for item in node
        ]

    elif isinstance(node, Object):
        return OrderedDict([
            (key, _document_to_primative(value)) for key, value in node.items()
            if not isinstance(value, (Document, Link))
        ])

    return node


class HALCodec(BaseCodec):
    media_type = "application/hal+json"

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

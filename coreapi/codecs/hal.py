from collections import OrderedDict
from coreapi.codecs.base import BaseCodec, _get_string, _get_dict, _get_bool
from coreapi.compat import force_bytes, urlparse
from coreapi.compat import COMPACT_SEPARATORS, VERBOSE_SEPARATORS
from coreapi.document import Document, Link, Array, Object, Field, Error
from coreapi.exceptions import ParseError
import json
import uritemplate


def _is_array_containing_instance(value, datatype):
    return isinstance(value, Array) and value and isinstance(value[0], datatype)


def _is_map_containing_instance(value, datatype):
    return isinstance(value, Object) and value and isinstance(value[0], datatype)


def _document_to_primative(node, base_url=None):
    if isinstance(node, Document):
        url = urlparse.urljoin(base_url, node.url)
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
                    if isinstance(item, Link)
                ]
            elif _is_map_containing_instance(value, Link):
                links[key] = {
                    key: _document_to_primative(val, base_url=url)
                    for key, val in value.items()
                    if isinstance(val, Link)
                }
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
        if embedded:
            ret['_embedded'] = embedded
        return ret

    elif isinstance(node, Link):
        url = urlparse.urljoin(base_url, node.url)
        ret = OrderedDict()
        ret['href'] = url
        templated = [field.name for field in node.fields if field.location == 'path']
        if templated:
            ret['href'] += "{?%s}" % ','.join([name for name in templated])
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

    elif isinstance(node, Error):
        return OrderedDict([
            (key, _document_to_primative(value)) for key, value in node.items()
        ])

    return node


def _parse_link(data, base_url=None):
    url = _get_string(data, 'href')
    url = urlparse.urljoin(base_url, url)
    if _get_bool(data, 'templated'):
        fields = [
            Field(name, location='path') for name in uritemplate.variables(url)
        ]
    else:
        fields = None
    return Link(url=url, fields=fields)


def _map_to_coreapi_key(key):
    # HAL uses 'rel' values to index links and nested resources.
    if key.startswith('http://') or key.startswith('https://'):
        # Fully qualified URL - just use last portion of the path.
        return urlparse.urlsplit(key).path.split('/')[-1]
    elif ':' in key:
        # A curried 'rel' value. Use the named portion.
        return key.split(':', 1)[1]
    # A reserved 'rel' value, such as "next".
    return key


def _parse_document(data, base_url=None):
    links = _get_dict(data, '_links')
    embedded = _get_dict(data, '_embedded')

    self = _get_dict(links, 'self')
    url = _get_string(self, 'href')
    url = urlparse.urljoin(base_url, url)
    title = _get_string(self, 'title')

    content = {}

    for key, value in links.items():
        if key in ('self', 'curies'):
            continue

        key = _map_to_coreapi_key(key)

        if isinstance(value, list):
            if value and 'name' in value[0]:
                # Lists of named links should be represented inside a map.
                content[key] = {
                    item['name']: _parse_link(item, base_url)
                    for item in value
                    if 'name' in item
                }
            else:
                # Lists of named links should be represented inside a list.
                content[key] = [
                    _parse_link(item, base_url)
                    for item in value
                ]
        elif isinstance(value, dict):
            # Single link instance.
            content[key] = _parse_link(value, base_url)

    # Embedded resources.
    for key, value in embedded.items():
        key = _map_to_coreapi_key(key)
        if isinstance(value, list):
            content[key] = [_parse_document(item, base_url=url) for item in value]
        elif isinstance(value, dict):
            content[key] = _parse_document(value, base_url=url)

    # Data.
    for key, value in data.items():
        if key not in ('_embedded', '_links'):
            content[key] = value

    return Document(url, title, content)


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

    def load(self, bytes, base_url=None):
        """
        Takes a bytestring and returns a document.
        """
        try:
            data = json.loads(bytes.decode('utf-8'))
        except ValueError as exc:
            raise ParseError('Malformed JSON. %s' % exc)

        doc = _parse_document(data, base_url)
        if not isinstance(doc, Document):
            raise ParseError('Top level node must be a document.')

        return doc

from collections import OrderedDict
from coreapi.codecs.base import BaseCodec
from coreapi.compat import force_bytes, urlparse
from coreapi.compat import COMPACT_SEPARATORS, VERBOSE_SEPARATORS
from coreapi.document import Document, Link, Array, Object
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
        ret['_embedded'] = embedded
        return ret

    elif isinstance(node, Link):
        url = urlparse.urljoin(base_url, node.url)
        ret = OrderedDict()
        ret['href'] = url
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


def _parse_link(data, base_url=None):
    url = urlparse.urljoin(base_url, data.get('href'))
    if data.get('templated'):
        fields = list(uritemplate.variables(url))
    else:
        fields = None
    return Link(url=url, fields=fields)


def _parse_document(data, base_url=None):
    self = data.get('_links', {}).get('self')
    if not self:
        url = base_url
        title = None
    else:
        url = urlparse.urljoin(base_url, self.get('href'))
        title = self.get('title')

    content = {}

    for key, value in data.get('_links', {}).items():
        if key in ('self', 'curies', 'curie'):
            continue

        if ':' in key:
            key = key.split(':', 1)[1]

        if isinstance(value, list):
            if value and 'name' in value[0]:
                content[key] = {item['name']: _parse_link(item, base_url) for item in value}
            else:
                content[key] = [_parse_link(item, base_url) for item in value]
        elif isinstance(value, dict):
            content[key] = _parse_link(value, base_url)

    for key, value in data.get('_embedded', {}):
        if isinstance(value, list):
            content[key] = [_parse_document(item, base_url=url) for item in value]
        elif isinstance(value, dict):
            content[key] = _parse_document(value, base_url=url)

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
            raise ParseError('Top level node must be a document message.')

        return doc

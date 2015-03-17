# coding: utf-8
from collections import OrderedDict
from coreapi.compat import is_string, urlparse
from coreapi.document import Document, Link, Array, Object
from coreapi.exceptions import ParseError
import json


class DocJSONCodec:
    media_type = 'application/vnd.document+json'

    def loads(self, bytes, base_url=None):
        """
        Takes a bytestring and returns a document.
        """
        # TODO: Assert base_url has a scheme if used.

        try:
            data = json.loads(bytes, object_pairs_hook=OrderedDict)
        except ValueError as exc:
            raise ParseError('Malformed JSON - ' + str(exc))

        # The returned JSON MUST be a document.
        if not isinstance(data, OrderedDict):
            raise ParseError('Expected a DocJSON document, but got %s' % type(data).__name__)
        if '_type' not in data:
            raise ParseError('Document missing "_type": "document"')
        if data['_type'] != 'document':
            raise ParseError('Document should have "_type": "document", but had incorrect "_type": "%s"' % data['_type'])

        return self._parse_document(data, base_url)

    def dumps(self, document, indent=None):
        """
        Takes a document and returns a bytestring.
        """
        return json.dumps(document, cls=_CustomJSONEncoder, indent=indent)

    def _parse(self, data, base_url):
        """
        Given some parsed JSON data, returns the corresponding DocJSON objects.
        """
        if isinstance(data, OrderedDict) and data.get('_type') == 'document':
            return self._parse_document(data, base_url)
        elif isinstance(data, OrderedDict) and data.get('_type') == 'link':
            return self._parse_link(data, base_url)
        elif isinstance(data, OrderedDict):
            return self._parse_object(data, base_url)
        elif isinstance(data, list):
            return self._parse_list(data, base_url)
        return data

    def _parse_document(self, data, base_url=None):
        # Documents MUST have a valid `.meta.url` attribute.
        if 'meta' not in data:
            raise ParseError('Document missing "meta" attribute')
        if not isinstance(data['meta'], OrderedDict):
            raise ParseError('Document "meta" attribute should be an object but got %s' % type(data['meta']).__name__)
        if '_type' in data['meta']:
            raise ParseError('Document "meta" attribute should be a plain json object, not "_type": "%s"' % data['meta']['_type'])
        if 'url' not in data['meta']:
            raise ParseError('Document missing "meta.url" attribute')
        if not is_string(data['meta']['url']):
            raise ParseError('Document "meta.url" attribute should be a string, but got %s' % type(data['meta']['url']).__name__)

        url = data['meta']['url']
        if base_url:
            url = urlparse.urljoin(base_url, url)
            data['meta']['url'] = url

        return Document([
            (key, self._parse(value, base_url=url))
            for key, value in data.items()
        ])

    def _parse_link(self, data, base_url):
        url, rel, fields = None, None, None

        # A link MAY contain `url`, `rel` and `fields` attributes.
        if 'url' in data and is_string(data['url']):
            url = data['url']
        if 'rel' in data and is_string(data['rel']):
            rel = data['rel']
        if 'fields' in data and isinstance(data['fields'], list):
            fields = [
                field if isinstance(field, dict) else {'name': str(field)}
                for field
                in data['fields']
            ]

        url = urlparse.urljoin(base_url, url)

        # TODO: Validate field dicts are properly formed
        # TODO: Validate field names are strings
        # TODO: Validate field names match regex '[A-Za-z_][A-Za-z0-9_]*'
        # TODO: Validate field required is bool

        return Link(url, rel, fields)

    def _parse_object(self, data, base_url):
        # Parse all the items in the dict and wrap them in a `Object`.
        return Object([
            (key, self._parse(value, base_url))
            for key, value in data.items()
        ])

    def _parse_list(self, data, base_url):
        # Parse all the items in the list and wrap them in a `List`.
        parsed = []
        for item in data:
            value = self._parse(item, base_url)
            # Ignore 'Link' objects contained in a list.
            if not isinstance(value, Link):
                parsed.append(value)
        return Array(parsed)


class _CustomJSONEncoder(json.JSONEncoder):
    def encode(self, obj):
        if isinstance(obj, Document):
            ret = OrderedDict()
            ret['_type'] = 'document'
            ret['meta'] = obj.get('meta', {})
            ret.update(obj)
            return super(_CustomJSONEncoder, self).encode(ret)
        return super(_CustomJSONEncoder, self).encode(obj)

    def default(self, obj):
        if isinstance(obj, Link):
            ret = OrderedDict()
            ret['_type'] = 'link'
            ret['url'] = obj.url
            if obj.method != 'GET':
                ret['method'] = obj.method
            if obj.fields:
                ret['fields'] = obj.fields
            return ret
        return super(_CustomJSONEncoder, self).default(obj)

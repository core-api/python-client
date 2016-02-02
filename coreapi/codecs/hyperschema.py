# coding: utf-8
from coreapi.codecs.base import BaseCodec, _get_string, _get_list, _get_dict, get_dicts
from coreapi.compat import urlparse
from coreapi.document import Document, Link, Field
from coreapi.exceptions import ParseError
import json
import uritemplate
import urllib


def _dereference(value, ref):
    keys = value.strip('#/').split('/')
    node = ref
    for key in keys:
        node = _get_dict(node, key)
    return node


def _get_content(data, base_url, ref):
    content = {}
    links = _get_list(data, 'links')
    properties = _get_dict(data, 'properties')

    if properties:
        for key, value in properties.items():
            if not isinstance(value, dict):
                continue
            if list(value.keys()) == ['$ref']:
                value = _dereference(value['$ref'], ref)
            sub_content = _get_content(value, base_url, ref)
            if sub_content:
                content[key] = sub_content
    if links:
        for link in get_dicts(links):
            rel = _get_string(link, 'rel')
            if rel:
                href = _get_string(link, 'href')
                method = _get_string(link, 'method')
                schema = _get_dict(link, 'schema')
                schema_type = _get_list(schema, 'type')
                schema_properties = _get_dict(schema, 'properties')
                schema_required = _get_list(schema, 'required')

                fields = []
                url = urlparse.urljoin(base_url, href)
                templated = uritemplate.variables(url)
                for item in templated:
                    orig = item
                    if item.startswith('(') and item.endswith(')'):
                        item = urllib.unquote(item.strip('(').rstrip(')'))
                    if item.startswith('#/'):
                        components = [
                            component for component in item.strip('#/').split('/')
                            if component != 'definitions'
                        ]
                    item = '_'.join(components).replace('-', '_')
                    url = url.replace(orig, item)
                    fields.append(Field(name=item, location='path', required=True))

                if schema_type == ['object'] and schema_properties:
                    fields += [
                        Field(name=key, required=(key in schema_required))
                        for key in schema_properties.keys()
                    ]
                if rel == 'self':
                    rel = 'read'
                content[rel] = Link(url=url, action=method, fields=fields)

    return content


def _primative_to_document(data, base_url):
    url = base_url

    # Determine if the document contains a self URL.
    links = _get_list(data, 'links')
    for link in get_dicts(links):
        href = _get_string(link, 'href')
        rel = _get_string(link, 'rel')
        if rel == 'self' and href:
            url = urlparse.urljoin(url, href)

    # Load the document content.
    title = _get_string(data, 'title')
    content = _get_content(data, url, ref=data)
    return Document(title=title, url=url, content=content)


class HyperschemaCodec(BaseCodec):
    """
    JSON Hyper-Schema.
    """
    media_type = 'application/schema+json'

    def load(self, bytes, base_url=None):
        """
        Takes a bytestring and returns a document.
        """
        try:
            data = json.loads(bytes.decode('utf-8'))
        except ValueError as exc:
            raise ParseError('Malformed JSON. %s' % exc)

        doc = _primative_to_document(data, base_url)
        if not (isinstance(doc, Document)):
            raise ParseError('Top level node must be a document.')

        return doc

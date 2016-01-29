from coreapi.codecs.base import BaseCodec, _get_string, _get_dict, _get_list, _get_bool, get_strings, get_dicts
from coreapi.compat import urlparse
from coreapi.document import Document, Link, Array, Object, Field, Error
from coreapi.exceptions import ParseError
import json


def expand_schema(schema):
    schema_type = schema.get('type')
    schema_properties = _get_dict(schema, 'properties')
    schema_required = _get_list(schema, 'required')
    if ((schema_type == ['object']) or (schema_type == 'object')) and schema_properties:
        return [
            (key, key in schema_required)
            for key in schema_properties.keys()
        ]
    return None


def _get_document_base_url(data, base_url=None):
    prefered_schemes = ['http', 'https']
    if base_url:
        url_components = urlparse.urlparse(base_url)
        default_host = url_components.netloc
        default_scheme = url_components.scheme
    else:
        default_host = ''
        default_scheme = None

    host = _get_string(data, 'host', default=default_host)
    path = _get_string(data, 'basePath', default='/')

    if not host:
        # No host is provided, and we do not have an initial URL.
        return path

    schemes = _get_list(data, 'schemes')

    if not schemes:
        # No schemes provided, use the initial URL, or a fallback.
        scheme = default_scheme or prefered_schemes[0]
    elif default_scheme in schemes:
        # Schemes provided, the initial URL matches one of them.
        scheme = default_scheme
    else:
        # Schemes provided, the initial URL does not match, pick a fallback.
        for scheme in prefered_schemes:
            if scheme in schemes:
                break
        else:
            raise ParseError('Unsupported transport schemes "%s"' % schemes)

    return '%s://%s/%s' % (scheme, host, path.lstrip('/'))


def _parse_document(data, base_url=None):
    schema_url = base_url
    base_url = _get_document_base_url(data, base_url)
    info = _get_dict(data, 'info')
    title = _get_string(info, 'title')
    paths = _get_dict(data, 'paths')
    content = {}
    for path in paths.keys():
        url = urlparse.urljoin(base_url, path)
        spec = _get_dict(paths, path)
        default_parameters = get_dicts(_get_list(spec, 'parameters'))
        for action in spec.keys():
            action = action.lower()
            if action not in ('get', 'put', 'post', 'delete', 'options', 'head', 'patch'):
                continue
            operation = _get_dict(spec, action)

            # Determine any fields on the link.
            fields = []
            parameters = get_dicts(_get_list(operation, 'parameters'))
            for parameter in parameters:
                name = _get_string(parameter, 'name')
                location = _get_string(parameter, 'in')
                required = _get_bool(parameter, 'required')
                field = Field(name=name, location=location, required=required)
                fields.append(field)
                if location == 'body':
                    schema = _get_dict(parameter, 'schema', dereference_using=data)
                    expanded = expand_schema(schema)
                    if expanded is not None:
                        fields = [
                            Field(name=name, location='form', required=required)
                            for name, required in expanded
                        ]
                    else:
                        fields = [Field(name=name, required=True)]
            link = Link(url=url, action=action, fields=fields)

            # Add the link to the document content.
            tags = get_strings(_get_list(operation, 'tags'))
            operation_id = _get_string(operation, 'operationId')
            if tags:
                for tag in tags:
                    if tag not in content:
                        content[tag] = {}
                    content[tag][operation_id] = link
            else:
                content[operation_id] = link

    return Document(url=schema_url, title=title, content=content)


class OpenAPICodec(BaseCodec):
    media_type = "application/json"

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

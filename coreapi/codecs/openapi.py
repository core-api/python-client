from coreapi.codecs import BaseCodec, JSONSchemaCodec
from coreapi.compat import VERBOSE_SEPARATORS, dict_type, force_bytes, urlparse
from coreapi.document import Document, Link, Field
from coreapi.exceptions import ParseError
from coreapi.schemas import OpenAPI
import json


METHODS = [
    'get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace'
]


def _relative_url(base_url, url):
    """
    Return a graceful link for a URL relative to a base URL.

    * If the have the same scheme and hostname, return the path & query params.
    * Otherwise return the full URL.
    """
    base_prefix = '%s://%s' % urlparse.urlparse(base_url or '')[0:2]
    url_prefix = '%s://%s' % urlparse.urlparse(url or '')[0:2]
    if base_prefix == url_prefix and url_prefix != '://':
        return url[len(url_prefix):]
    return url


class OpenAPICodec(BaseCodec):
    media_type = 'application/vnd.oai.openapi'
    format = 'openapi'

    def decode(self, bytestring, **options):
        try:
            data = json.loads(bytestring.decode('utf-8'))
        except ValueError as exc:
            raise ParseError('Malformed JSON. %s' % exc)

        openapi = OpenAPI(data)
        title = openapi.lookup(['info', 'title'])
        description = openapi.lookup(['info', 'description'])
        version = openapi.lookup(['info', 'version'])
        base_url = openapi.lookup(['servers', 0, 'url'])
        content = self.get_links(openapi, base_url)
        return Document(title=title, description=description, version=version, url=base_url, content=content)

    def get_links(self, openapi, base_url):
        """
        Return all the links in the document, layed out by tag and operationId.
        """
        content = {}

        for path, path_info in openapi.get('paths', {}).items():
            operations = {
                key: path_info[key] for key in path_info
                if key in METHODS
            }
            for operation, operation_info in operations.items():
                operationId = operation_info.get('operationId')
                tag = operation_info.lookup(['tags', 0])
                if not operationId:
                    continue

                link = self.get_link(base_url, path, path_info, operation, operation_info)
                if tag is None:
                    content[operationId] = link
                else:
                    if tag in content:
                        content[tag][operationId] = link
                    else:
                        content[tag] = {operationId: link}

        return content

    def get_link(self, base_url, path, path_info, operation, operation_info):
        """
        Return a single link in the document.
        """
        title = operation_info.get('summary')
        description = operation_info.get('description')

        # Allow path info and operation info to override the base url.
        base_url = path_info.lookup(['servers', 0, 'url'], default=base_url)
        base_url = operation_info.lookup(['servers', 0, 'url'], default=base_url)

        # Parameters are taken both from the path info, and from the operation.
        parameters = path_info.get('parameters', [])
        parameters += operation_info.get('parameters', [])

        fields = [
            self.get_field(parameter)
            for parameter in parameters
        ]

        return Link(
            url=urlparse.urljoin(base_url, path),
            method=operation,
            title=title,
            description=description,
            fields=fields
        )

    def get_field(self, parameter):
        """
        Return a single field in a link.
        """
        name = parameter.get('name')
        location = parameter.get('in')
        description = parameter.get('description')
        required = parameter.get('required', False)
        schema = parameter.get('schema')
        example = parameter.get('example')

        if schema is not None:
            schema = JSONSchemaCodec().decode_from_data_structure(schema)

        return Field(
            name=name,
            location=location,
            description=description,
            required=required,
            schema=schema,
            example=example
        )

    def encode(self, document, **options):
        paths = self.get_paths(document)
        openapi = OpenAPI({
            'openapi': '3.0.0',
            'info': {
                'version': document.version,
                'title': document.title,
                'description': document.description
            },
            'servers': [{
                'url': document.url
            }],
            'paths': paths
        })

        kwargs = {
            'ensure_ascii': False,
            'indent': 4,
            'separators': VERBOSE_SEPARATORS
        }
        return force_bytes(json.dumps(openapi, **kwargs))

    def get_paths(self, document):
        paths = dict_type()

        for operation_id, link in document.links.items():
            url = urlparse.urlparse(link.url)
            if url.path not in paths:
                paths[url.path] = {}
            paths[url.path][link.action] = self.get_operation(link, operation_id)

        for tag, links in document.data.items():
            for operation_id, link in links.links.items():
                url = urlparse.urlparse(link.url)
                if url.path not in paths:
                    paths[url.path] = {}
                paths[url.path][link.action] = self.get_operation(link, operation_id, tag=tag)

        return paths

    def get_operation(self, link, operation_id, tag=None):
        operation = {
            'operationId': operation_id
        }
        if link.title:
            operation['summary'] = link.title
        if link.description:
            operation['description'] = link.description
        if tag:
            operation['tags'] = [tag]
        if link.fields:
            operation['parameters'] = [self.get_parameter(field) for field in link.fields]
        return operation

    def get_parameter(self, field):
        parameter = {
            'name': field.name,
            'in': field.location
        }
        if field.required:
            parameter['required'] = True
        if field.description:
            parameter['description'] = field.description
        if field.schema:
            parameter['schema'] = JSONSchemaCodec().encode_to_data_structure(field.schema)
        return parameter

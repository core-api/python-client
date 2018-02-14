from coreapi.codecs import BaseCodec, JSONSchemaCodec
from coreapi.compat import urlparse
from coreapi.document import Document, Link, Field
from coreapi.schemas import OpenAPI
import yaml


METHODS = [
    'get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace'
]


class OpenAPICodec(BaseCodec):
    media_type = 'application/vnd.oai.openapi'
    format = 'openapi'

    def decode(self, bytestring, **options):
        data = yaml.safe_load(bytestring)
        openapi = OpenAPI(data)
        title = openapi.lookup(['info', 'title'])
        description = openapi.lookup(['info', 'description'])
        base_url = openapi.lookup(['servers', 0, 'url'])
        content = self.get_links(openapi, base_url)
        return Document(title=title, description=description, url=base_url, content=content)

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
            action=operation,
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

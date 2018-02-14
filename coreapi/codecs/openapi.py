from coreapi.codecs import BaseCodec, JSONSchemaCodec
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
        url = openapi.lookup(['servers', 0, 'url'])
        content = self.get_links(openapi)
        return Document(title=title, description=description, url=url, content=content)

    def get_links(self, openapi):
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

                link = self.get_link(path, path_info, operation, operation_info)
                if tag is None:
                    content[operationId] = link
                else:
                    if tag in content:
                        content[tag][operationId] = link
                    else:
                        content[tag] = {operationId: link}

        return content

    def get_link(self, path, path_info, operation, operation_info):
        """
        Return a single link in the document.
        """
        title = operation_info.get('summary')
        description = operation_info.get('description')
        parameters = path_info.get('parameters', [])
        parameters += operation_info.get('parameters', [])

        fields = [
            self.get_field(parameter)
            for parameter in parameters
        ]

        return Link(
            url=path,
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

        if schema is not None:
            schema = JSONSchemaCodec().decode_from_data_structure(schema)

        return Field(
            name=name,
            location=location,
            description=description,
            required=required,
            schema=schema
        )

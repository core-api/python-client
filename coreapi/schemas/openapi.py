from coreapi import typesys
from coreapi.schemas import JSONSchema


SchemaRefString = typesys.String(pattern='^#/components/schemas/')


OpenAPI = typesys.Object(
    self_ref='OpenAPI',
    title='OpenAPI',
    properties=[
        ('openapi', typesys.String()),
        ('info', typesys.Ref('Info')),
        ('servers', typesys.Array(items=typesys.Ref('Server'))),
        ('paths', typesys.Ref('Paths')),
        ('components', typesys.Ref('Components')),
        ('security', typesys.Ref('SecurityRequirement')),
        ('tags', typesys.Array(items=typesys.Ref('Tag'))),
        ('externalDocs', typesys.Ref('ExternalDocumentation'))
    ],
    required=['openapi', 'info'],
    definitions={
        'Info': typesys.Object(
            properties=[
                ('title', typesys.String()),
                ('description', typesys.String(format='textarea')),
                ('termsOfService', typesys.String(format='url')),
                ('contact', typesys.Ref('Contact')),
                ('license', typesys.Ref('License')),
                ('version', typesys.String())
            ],
            required=['title', 'version']
        ),
        'Contact': typesys.Object(
            properties=[
                ('name', typesys.String()),
                ('url', typesys.String(format='url')),
                ('email', typesys.String(format='email'))
            ]
        ),
        'License': typesys.Object(
            properties=[
                ('name', typesys.String()),
                ('url', typesys.String(format='url'))
            ],
            required=['name']
        ),
        'Server': typesys.Object(
            properties=[
                ('url', typesys.String()),
                ('description', typesys.String(format='textarea')),
                ('variables', typesys.Object(additional_properties=typesys.Ref('ServerVariable')))
            ],
            required=['url']
        ),
        'ServerVariable': typesys.Object(
            properties=[
                ('enum', typesys.Array(items=typesys.String())),
                ('default', typesys.String()),
                ('description', typesys.String(format='textarea'))
            ],
            required=['default']
        ),
        'Paths': typesys.Object(
            pattern_properties=[
                ('^/', typesys.Ref('Path'))  # TODO: Path | ReferenceObject
            ]
        ),
        'Path': typesys.Object(
            properties=[
                ('summary', typesys.String()),
                ('description', typesys.String(format='textarea')),
                ('get', typesys.Ref('Operation')),
                ('put', typesys.Ref('Operation')),
                ('post', typesys.Ref('Operation')),
                ('delete', typesys.Ref('Operation')),
                ('options', typesys.Ref('Operation')),
                ('head', typesys.Ref('Operation')),
                ('patch', typesys.Ref('Operation')),
                ('trace', typesys.Ref('Operation')),
                ('servers', typesys.Array(items=typesys.Ref('Server'))),
                ('parameters', typesys.Array(items=typesys.Ref('Parameter')))  # TODO: Parameter | ReferenceObject
            ]
        ),
        'Operation': typesys.Object(
            properties=[
                ('tags', typesys.Array(items=typesys.String())),
                ('summary', typesys.String()),
                ('description', typesys.String(format='textarea')),
                ('externalDocs', typesys.Ref('ExternalDocumentation')),
                ('operationId', typesys.String()),
                ('parameters', typesys.Array(items=typesys.Ref('Parameter'))),  # TODO: Parameter | ReferenceObject
                ('requestBody', typesys.Ref('RequestBody')),  # TODO: RequestBody | ReferenceObject
                # TODO: 'responses'
                # TODO: 'callbacks'
                ('deprecated', typesys.Boolean()),
                ('security', typesys.Array(typesys.Ref('SecurityRequirement'))),
                ('servers', typesys.Array(items=typesys.Ref('Server')))
            ]
        ),
        'ExternalDocumentation': typesys.Object(
            properties=[
                ('description', typesys.String(format='textarea')),
                ('url', typesys.String(format='url'))
            ],
            required=['url']
        ),
        'Parameter': typesys.Object(
            properties=[
                ('name', typesys.String()),
                ('in', typesys.String(enum=['query', 'header', 'path', 'cookie'])),
                ('description', typesys.String(format='textarea')),
                ('required', typesys.Boolean()),
                ('deprecated', typesys.Boolean()),
                ('allowEmptyValue', typesys.Boolean()),
                ('schema', JSONSchema | SchemaRefString),
                ('example', typesys.Any())
                # TODO: Other fields
            ],
            required=['name', 'in']
        ),
        'RequestBody': typesys.Object(
            properties=[
                ('description', typesys.String()),
                ('content', typesys.Object(additional_properties=typesys.Ref('MediaType'))),
                ('required', typesys.Boolean())
            ]
        ),
        'MediaType': typesys.Object(
            properties=[
                ('schema', JSONSchema | SchemaRefString),
                ('example', typesys.Any())
                # TODO 'examples', 'encoding'
            ]
        ),
        'Components': typesys.Object(
            properties=[
                ('schemas', typesys.Object(additional_properties=JSONSchema)),
            ]
        ),
        'Tag': typesys.Object(
            properties=[
                ('name', typesys.String()),
                ('description', typesys.String(format='textarea')),
                ('externalDocs', typesys.Ref('ExternalDocumentation'))
            ],
            required=['name']
        ),
        'SecurityRequirement': typesys.Object(
            additional_properties=typesys.Array(items=typesys.String())
        )
    }
)

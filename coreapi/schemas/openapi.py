from coreapi import typesys
from coreapi.schemas import JSONSchema


Contact = typesys.Object(
    properties=[
        ('name', typesys.String()),
        ('url', typesys.String(format='url')),
        ('email', typesys.String(format='email'))
    ]
)


License = typesys.Object(
    properties=[
        ('name', typesys.String()),
        ('url', typesys.String(format='url'))
    ],
    required=['name']
)


Info = typesys.Object(
    properties=[
        ('title', typesys.String()),
        ('description', typesys.String(format='textarea')),
        ('termsOfService', typesys.String(format='url')),
        ('contact', Contact),
        ('license', License),
        ('version', typesys.String())
    ],
    required=['title', 'version']
)


ServerVariable = typesys.Object(
    properties=[
        ('enum', typesys.Array(items=typesys.String())),
        ('default', typesys.String()),
        ('description', typesys.String(format='textarea'))
    ],
    required=['default']
)


Server = typesys.Object(
    properties=[
        ('url', typesys.String()),
        ('description', typesys.String(format='textarea')),
        ('variables', typesys.Object(additional_properties=ServerVariable))
    ],
    required=['url']
)


ExternalDocs = typesys.Object(
    properties=[
        ('description', typesys.String(format='textarea')),
        ('url', typesys.String(format='url'))
    ],
    required=['url']
)


SecurityRequirement = typesys.Object(
    additional_properties=typesys.Array(items=typesys.String())
)


Parameter = typesys.Object(
    properties=[
        ('name', typesys.String()),
        ('in', typesys.String(enum=['query', 'header', 'path', 'cookie'])),
        ('description', typesys.String(format='textarea')),
        ('required', typesys.Boolean()),
        ('deprecated', typesys.Boolean()),
        ('allowEmptyValue', typesys.Boolean()),
        ('schema', JSONSchema),
        ('example', typesys.Any())
        # TODO: Other fields
    ],
    required=['name', 'in']
)


Operation = typesys.Object(
    properties=[
        ('tags', typesys.Array(items=typesys.String())),
        ('summary', typesys.String()),
        ('description', typesys.String(format='textarea')),
        ('externalDocs', ExternalDocs),
        ('operationId', typesys.String()),
        ('parameters', typesys.Array(items=Parameter)),  # TODO: Parameter | ReferenceObject
        # TODO: 'requestBody'
        # TODO: 'responses'
        # TODO: 'callbacks'
        ('deprecated', typesys.Boolean()),
        ('security', SecurityRequirement),
        ('servers', typesys.Array(items=Server))
    ]
)


Path = typesys.Object(
    properties=[
        ('summary', typesys.String()),
        ('description', typesys.String(format='textarea')),
        ('get', Operation),
        ('put', Operation),
        ('post', Operation),
        ('delete', Operation),
        ('options', Operation),
        ('head', Operation),
        ('patch', Operation),
        ('trace', Operation),
        ('servers', typesys.Array(items=Server)),
        ('parameters', typesys.Array(items=Parameter))  # TODO: Parameter | ReferenceObject
    ]
)


Paths = typesys.Object(
    pattern_properties=[
        ('^/', Path)  # TODO: Path | ReferenceObject
    ]
)


Tag = typesys.Object(
    properties=[
        ('name', typesys.String()),
        ('description', typesys.String(format='textarea')),
        ('externalDocs', ExternalDocs)
    ],
    required=['name']
)


OpenAPI = typesys.Object(
    properties=[
        ('openapi', typesys.String()),
        ('info', Info),
        ('servers', typesys.Array(items=Server)),
        ('paths', Paths),
        # TODO: 'components': ...,
        ('security', SecurityRequirement),
        ('tags', typesys.Array(items=Tag)),
        ('externalDocs', ExternalDocs)
    ],
    required=['openapi', 'info']
)

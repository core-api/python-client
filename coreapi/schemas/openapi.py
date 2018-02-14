from coreapi import typesys
from coreapi.schemas import JSONSchema


class Contact(typesys.Object):
    properties = {
        'name': typesys.string(),
        'url': typesys.string(format='url'),
        'email': typesys.string(format='email')
    }


class License(typesys.Object):
    properties = {
        'name': typesys.string(),
        'url': typesys.string(format='url')
    }
    required = ['name']


class Info(typesys.Object):
    properties = {
        'title': typesys.string(),
        'description': typesys.string(format='textarea'),
        'termsOfService': typesys.string(format='url'),
        'contact': Contact,
        'license': License,
        'version': typesys.string()
    }
    required = ['title', 'version']


class ServerVariable(typesys.Object):
    properties = {
        'enum': typesys.array(items=typesys.string()),
        'default': typesys.string(),
        'description': typesys.string(format='textarea')
    }
    required = ['default']


class Server(typesys.Object):
    properties = {
        'url': typesys.string(),
        'description': typesys.string(format='textarea'),
        'variables': typesys.obj(additional_properties=ServerVariable)
    }
    required = ['url']


class ExternalDocs(typesys.Object):
    properties = {
        'description': typesys.string(format='textarea'),
        'url': typesys.string(format='url')
    }
    required = ['url']


class SecurityRequirement(typesys.Object):
    additional_properties = typesys.array(items=typesys.string())


class Parameter(typesys.Object):
    properties = {
        'name': typesys.string(),
        'in': typesys.enum(enum=['query', 'header', 'path', 'cookie']),
        'description': typesys.string(format='textarea'),
        'required': typesys.boolean(),
        'deprecated': typesys.boolean(),
        'allowEmptyValue': typesys.boolean(),
        'schema': JSONSchema,
        # TODO: Other fields
    }
    required = ['name', 'in']


class Operation(typesys.Object):
    properties = {
        'tags': typesys.array(items=typesys.string()),
        'summary': typesys.string(),
        'description': typesys.string(format='textarea'),
        'externalDocs': ExternalDocs,
        'operationId': typesys.string(),
        'parameters': typesys.array(items=Parameter),  # Parameter | ReferenceObject
        # TODO: 'requestBody'
        # TODO: 'responses'
        # TODO: 'callbacks'
        'deprecated': typesys.boolean(),
        'security': SecurityRequirement,
        'servers': typesys.array(items=Server)
    }


class Path(typesys.Object):
    properties = {
        'summary': typesys.string(),
        'description': typesys.string(format='textarea'),
        'get': Operation,
        'put': Operation,
        'post': Operation,
        'delete': Operation,
        'options': Operation,
        'head': Operation,
        'patch': Operation,
        'trace': Operation,
        'servers': typesys.array(items=Server),
        'parameters': typesys.array(items=Parameter)  # TODO: Parameter | ReferenceObject
    }


class Paths(typesys.Object):
    pattern_properties = {
        '^/': Path  # TODO: Path | ReferenceObject
    }


class Tag(typesys.Object):
    properties = {
        'name': typesys.string(),
        'description': typesys.string(format='textarea'),
        'externalDocs': ExternalDocs
    }
    required = ['name']


class OpenAPI(typesys.Object):
    properties = {
        'openapi': typesys.string(),
        'info': Info,
        'servers': typesys.array(items=Server),
        'paths': Paths,
        # TODO: 'components': ...,
        'security': SecurityRequirement,
        'tags': typesys.array(items=Tag),
        'externalDocs': ExternalDocs
    }
    required = ['openapi', 'info']

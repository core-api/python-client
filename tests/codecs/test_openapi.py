from coreapi import typesys
from coreapi.codecs import OpenAPICodec
from coreapi.compat import dict_type
from coreapi.document import Document, Link, Field
import pytest


@pytest.fixture
def openapi_codec():
    return OpenAPICodec()


@pytest.fixture
def petstore_schema():
    return b'''{
    "openapi": "3.0.0",
    "info": {
        "title": "Swagger Petstore",
        "version": "1.0.0",
        "license": {
            "name": "MIT"
        }
    },
    "servers": [
        {
            "url": "http://petstore.swagger.io/v1"
        }
    ],
    "paths": {
        "/pets": {
            "get": {
                "tags": [
                    "pets"
                ],
                "summary": "List all pets",
                "operationId": "listPets",
                "parameters": [
                    {
                        "in": "query",
                        "description": "How many items to return at one time (max 100)",
                        "name": "limit",
                        "schema": {
                            "format": "int32",
                            "type": "integer"
                        },
                        "required": false
                    }
                ],
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Pets"
                                }
                            }
                        },
                        "description": "An paged array of pets",
                        "headers": {
                            "x-next": {
                                "description": "A link to the next page of responses",
                                "schema": {
                                    "type": "string"
                                }
                            }
                        }
                    },
                    "default": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Error"
                                }
                            }
                        },
                        "description": "unexpected error"
                    }
                }
            },
            "post": {
                "tags": [
                    "pets"
                ],
                "summary": "Create a pet",
                "operationId": "createPets",
                "responses": {
                    "201": {
                        "description": "Null response"
                    },
                    "default": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Error"
                                }
                            }
                        },
                        "description": "unexpected error"
                    }
                }
            }
        },
        "/pets/{petId}": {
            "get": {
                "tags": [
                    "pets"
                ],
                "summary": "Info for a specific pet",
                "operationId": "showPetById",
                "parameters": [
                    {
                        "in": "path",
                        "description": "The id of the pet to retrieve",
                        "name": "petId",
                        "schema": {
                            "type": "string"
                        },
                        "required": true
                    }
                ],
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Pets"
                                }
                            }
                        },
                        "description": "Expected response to a valid request"
                    },
                    "default": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Error"
                                }
                            }
                        },
                        "description": "unexpected error"
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "Error": {
                "properties": {
                    "code": {
                        "format": "int32",
                        "type": "integer"
                    },
                    "message": {
                        "type": "string"
                    }
                },
                "required": [
                    "code",
                    "message"
                ]
            },
            "Pets": {
                "items": {
                    "$ref": "#/components/schemas/Pet"
                },
                "type": "array"
            },
            "Pet": {
                "properties": {
                    "tag": {
                        "type": "string"
                    },
                    "id": {
                        "format": "int64",
                        "type": "integer"
                    },
                    "name": {
                        "type": "string"
                    }
                },
                "required": [
                    "id",
                    "name"
                ]
            }
        }
    }
}'''


@pytest.fixture
def minimal_petstore_schema():
    return b'''{
    "openapi": "3.0.0",
    "info": {
        "title": "Swagger Petstore",
        "description": "",
        "version": ""
    },
    "servers": [
        {
            "url": "http://petstore.swagger.io/v1"
        }
    ],
    "paths": {
        "/pets": {
            "get": {
                "tags": [
                    "pets"
                ],
                "summary": "List all pets",
                "operationId": "listPets",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "How many items to return at one time (max 100)",
                        "schema": {
                            "type": "integer",
                            "format": "int32"
                        }
                    }
                ]
            },
            "post": {
                "tags": [
                    "pets"
                ],
                "summary": "Create a pet",
                "operationId": "createPets"
            }
        },
        "/pets/{petId}": {
            "get": {
                "tags": [
                    "pets"
                ],
                "summary": "Info for a specific pet",
                "operationId": "showPetById",
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "description": "The id of the pet to retrieve",
                        "required": true,
                        "schema": {
                            "type": "string"
                        }
                    }
                ]
            }
        }
    }
}'''


def test_decode_openapi(openapi_codec, petstore_schema):
    doc = openapi_codec.decode(petstore_schema)
    expected = Document(
        title='Swagger Petstore',
        url='http://petstore.swagger.io/v1',
        content={
            'pets': dict_type([
                ('listPets', Link(
                    action='get',
                    url='http://petstore.swagger.io/pets',
                    title='List all pets',
                    fields=[
                        Field(
                            name='limit',
                            location='query',
                            description='How many items to return at one time (max 100)',
                            required=False,
                            schema=typesys.integer(format='int32')
                        )
                    ]
                )),
                ('createPets', Link(
                    action='post',
                    url='http://petstore.swagger.io/pets',
                    title='Create a pet'
                )),
                ('showPetById', Link(
                    action='get',
                    url='http://petstore.swagger.io/pets/{petId}',
                    title='Info for a specific pet',
                    fields=[
                        Field(
                            name='petId',
                            location='path',
                            description='The id of the pet to retrieve',
                            required=True,
                            schema=typesys.string()
                        )
                    ]
                ))
            ])
        }
    )
    assert doc == expected


def test_encode_openapi(openapi_codec, minimal_petstore_schema):
    doc = Document(
        title='Swagger Petstore',
        url='http://petstore.swagger.io/v1',
        content={
            'pets': {
                'listPets': Link(
                    action='get',
                    url='http://petstore.swagger.io/pets',
                    title='List all pets',
                    fields=[
                        Field(
                            name='limit',
                            location='query',
                            description='How many items to return at one time (max 100)',
                            required=False,
                            schema=typesys.integer(format='int32')
                        )
                    ]
                ),
                'createPets': Link(
                    action='post',
                    url='http://petstore.swagger.io/pets',
                    title='Create a pet'
                ),
                'showPetById': Link(
                    action='get',
                    url='http://petstore.swagger.io/pets/{petId}',
                    title='Info for a specific pet',
                    fields=[
                        Field(
                            name='petId',
                            location='path',
                            description='The id of the pet to retrieve',
                            required=True,
                            schema=typesys.string()
                        )
                    ]
                )
            }
        }
    )
    schema = openapi_codec.encode(doc)
    assert schema == minimal_petstore_schema

from coreapi import typesys
from coreapi.codecs import OpenAPICodec
from coreapi.document import Document, Link, Field
import pytest


@pytest.fixture
def openapi_codec():
    return OpenAPICodec()


@pytest.fixture
def petstore_schema():
    return '''
openapi: "3.0.0"
info:
  version: 1.0.0
  title: Swagger Petstore
  license:
    name: MIT
servers:
  - url: http://petstore.swagger.io/v1
paths:
  /pets:
    get:
      summary: List all pets
      operationId: listPets
      tags:
        - pets
      parameters:
        - name: limit
          in: query
          description: How many items to return at one time (max 100)
          required: false
          schema:
            type: integer
            format: int32
      responses:
        '200':
          description: An paged array of pets
          headers:
            x-next:
              description: A link to the next page of responses
              schema:
                type: string
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Pets"
        default:
          description: unexpected error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
    post:
      summary: Create a pet
      operationId: createPets
      tags:
        - pets
      responses:
        '201':
          description: Null response
        default:
          description: unexpected error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
  /pets/{petId}:
    get:
      summary: Info for a specific pet
      operationId: showPetById
      tags:
        - pets
      parameters:
        - name: petId
          in: path
          required: true
          description: The id of the pet to retrieve
          schema:
            type: string
      responses:
        '200':
          description: Expected response to a valid request
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Pets"
        default:
          description: unexpected error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
components:
  schemas:
    Pet:
      required:
        - id
        - name
      properties:
        id:
          type: integer
          format: int64
        name:
          type: string
        tag:
          type: string
    Pets:
      type: array
      items:
        $ref: "#/components/schemas/Pet"
    Error:
      required:
        - code
        - message
      properties:
        code:
          type: integer
          format: int32
        message:
          type: string
'''


def test_openapi(openapi_codec, petstore_schema):
    doc = openapi_codec.decode(petstore_schema)
    expected = Document(
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
    assert doc == expected

from coreapi import typesys
from coreapi.codecs.base import BaseCodec
from coreapi.compat import COMPACT_SEPARATORS, VERBOSE_SEPARATORS, force_bytes
from coreapi.exceptions import ParseError
from coreapi.schemas import JSONSchema
import collections
import json


class JSONSchemaCodec(BaseCodec):
    media_type = 'application/schema+json'

    def decode(self, bytestring, **options):
        try:
            data = json.loads(
                bytestring.decode('utf-8'),
                object_pairs_hook=collections.OrderedDict
            )
        except ValueError as exc:
            raise ParseError('Malformed JSON. %s' % exc)
        jsonschema = JSONSchema(data)
        return self.decode_from_data_structure(jsonschema)

    def decode_from_data_structure(self, struct):
        attrs = {}

        if '$ref' in struct:
            if struct['$ref'] == '#':
                return typesys.ref()
            name = struct['$ref'].split('/')[-1]
            return typesys.ref(name)

        if struct['type'] == 'string':
            if 'minLength' in struct:
                attrs['min_length'] = struct['minLength']
            if 'maxLength' in struct:
                attrs['max_length'] = struct['maxLength']
            if 'pattern' in struct:
                attrs['pattern'] = struct['pattern']
            if 'format' in struct:
                attrs['format'] = struct['format']
            return typesys.string(**attrs)

        if struct['type'] in ['number', 'integer']:
            if 'minimum' in struct:
                attrs['minimum'] = struct['minimum']
            if 'maximum' in struct:
                attrs['maximum'] = struct['maximum']
            if 'exclusiveMinimum' in struct:
                attrs['exclusiveMinimum'] = struct['exclusiveMinimum']
            if 'exclusiveMaximum' in struct:
                attrs['exclusiveMaximum'] = struct['exclusiveMaximum']
            if 'multipleOf' in struct:
                attrs['multipleOf'] = struct['multipleOf']
            if 'format' in struct:
                attrs['format'] = struct['format']
            if struct['type'] == 'integer':
                return typesys.integer(**attrs)
            return typesys.number(**attrs)

        if struct['type'] == 'boolean':
            return typesys.boolean()

        if struct['type'] == 'object':
            if 'properties' in struct:
                attrs['properties'] = {
                    key: self.decode_from_data_structure(value)
                    for key, value in struct['properties'].items()
                }
            if 'required' in struct:
                attrs['required'] = struct['required']
            return typesys.obj(**attrs)

        if struct['type'] == 'array':
            if 'items' in struct:
                attrs['items'] = self.decode_from_data_structure(struct['items'])
            if 'additionalItems' in struct:
                attrs['additional_items'] = struct['additionalItems']
            if 'minItems' in struct:
                attrs['min_items'] = struct['minItems']
            if 'maxItems' in struct:
                attrs['max_items'] = struct['maxItems']
            if 'uniqueItems' in struct:
                attrs['unique_items'] = struct['uniqueItems']
            return typesys.array(**attrs)

    def encode(self, cls, **options):
        struct = self.encode_to_data_structure(cls)
        indent = options.get('indent')
        if indent:
            kwargs = {
                'ensure_ascii': False,
                'indent': 4,
                'separators': VERBOSE_SEPARATORS
            }
        else:
            kwargs = {
                'ensure_ascii': False,
                'indent': None,
                'separators': COMPACT_SEPARATORS
            }
        return force_bytes(json.dumps(struct, **kwargs))

    def encode_to_data_structure(self, cls):
        if issubclass(cls, typesys.String):
            value = {'type': 'string'}
            if cls.max_length is not None:
                value['maxLength'] = cls.max_length
            if cls.min_length is not None:
                value['minLength'] = cls.min_length
            if cls.pattern is not None:
                value['pattern'] = cls.pattern
            if cls.format is not None:
                value['format'] = cls.format
            return value

        if issubclass(cls, typesys.NumericType):
            if issubclass(cls, typesys.Integer):
                value = {'type': 'integer'}
            else:
                value = {'type': 'number'}

            if cls.minimum is not None:
                value['minimum'] = cls.minimum
            if cls.maximum is not None:
                value['maximum'] = cls.maximum
            if cls.exclusive_minimum:
                value['exclusiveMinimum'] = cls.exclusive_minimum
            if cls.exclusive_maximum:
                value['exclusiveMaximum'] = cls.exclusive_maximum
            if cls.multiple_of is not None:
                value['multipleOf'] = cls.multiple_of
            if cls.format is not None:
                value['format'] = cls.format
            return value

        if issubclass(cls, typesys.Boolean):
            return {'type': 'boolean'}

        if issubclass(cls, typesys.Object):
            value = {'type': 'object'}
            if cls.properties:
                value['properties'] = {
                    key: self.encode_to_data_structure(value)
                    for key, value in cls.properties.items()
                }
            if cls.required:
                value['required'] = cls.required
            return value

        if issubclass(cls, typesys.Array):
            value = {'type': 'array'}
            if cls.items is not None:
                value['items'] = self.encode_to_data_structure(cls.items)
            if cls.additional_items:
                value['additionalItems'] = cls.additional_items
            if cls.min_items is not None:
                value['minItems'] = cls.min_items
            if cls.max_items is not None:
                value['maxItems'] = cls.max_items
            if cls.unique_items is not None:
                value['uniqueItems'] = cls.unique_items
            return value

        if issubclass(cls, typesys.Ref):
            if not cls.to:
                return {'$ref': '#'}
            return {'$ref': '#/definitions/%s' % cls.to}

        raise Exception('Cannot encode class %s' % cls)

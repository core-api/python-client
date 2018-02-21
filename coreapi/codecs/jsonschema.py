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
        jsonschema = JSONSchema.validate(data)
        return self.decode_from_data_structure(jsonschema)

    def decode_from_data_structure(self, struct):
        attrs = {}

        # if '$ref' in struct:
        #     if struct['$ref'] == '#':
        #         return typesys.ref()
        #     name = struct['$ref'].split('/')[-1]
        #     return typesys.ref(name)

        if struct['type'] == 'string':
            if 'minLength' in struct:
                attrs['min_length'] = struct['minLength']
            if 'maxLength' in struct:
                attrs['max_length'] = struct['maxLength']
            if 'pattern' in struct:
                attrs['pattern'] = struct['pattern']
            if 'format' in struct:
                attrs['format'] = struct['format']
            return typesys.String(**attrs)

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
                return typesys.Integer(**attrs)
            return typesys.Number(**attrs)

        if struct['type'] == 'boolean':
            return typesys.Boolean()

        if struct['type'] == 'object':
            if 'properties' in struct:
                attrs['properties'] = {
                    key: self.decode_from_data_structure(value)
                    for key, value in struct['properties'].items()
                }
            if 'required' in struct:
                attrs['required'] = struct['required']
            return typesys.Object(**attrs)

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
            return typesys.Array(**attrs)

    def encode(self, item, **options):
        struct = self.encode_to_data_structure(item)
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

    def encode_to_data_structure(self, item):
        if isinstance(item, typesys.String):
            value = {'type': 'string'}
            if item.max_length is not None:
                value['maxLength'] = item.max_length
            if item.min_length is not None:
                value['minLength'] = item.min_length
            if item.pattern is not None:
                value['pattern'] = item.pattern
            if item.format is not None:
                value['format'] = item.format
            return value

        if isinstance(item, typesys.NumericType):
            if isinstance(item, typesys.Integer):
                value = {'type': 'integer'}
            else:
                value = {'type': 'number'}

            if item.minimum is not None:
                value['minimum'] = item.minimum
            if item.maximum is not None:
                value['maximum'] = item.maximum
            if item.exclusive_minimum:
                value['exclusiveMinimum'] = item.exclusive_minimum
            if item.exclusive_maximum:
                value['exclusiveMaximum'] = item.exclusive_maximum
            if item.multiple_of is not None:
                value['multipleOf'] = item.multiple_of
            if item.format is not None:
                value['format'] = item.format
            return value

        if isinstance(item, typesys.Boolean):
            return {'type': 'boolean'}

        if isinstance(item, typesys.Object):
            value = {'type': 'object'}
            if item.properties:
                value['properties'] = {
                    key: self.encode_to_data_structure(value)
                    for key, value in item.properties.items()
                }
            if item.required:
                value['required'] = item.required
            return value

        if isinstance(item, typesys.Array):
            value = {'type': 'array'}
            if item.items is not None:
                value['items'] = self.encode_to_data_structure(item.items)
            if item.additional_items:
                value['additionalItems'] = item.additional_items
            if item.min_items is not None:
                value['minItems'] = item.min_items
            if item.max_items is not None:
                value['maxItems'] = item.max_items
            if item.unique_items is not None:
                value['uniqueItems'] = item.unique_items
            return value

        raise Exception('Cannot encode item %s' % item)

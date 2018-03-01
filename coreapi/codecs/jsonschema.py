from coreapi import typesys
from coreapi.codecs.base import BaseCodec
from coreapi.compat import COMPACT_SEPARATORS, VERBOSE_SEPARATORS, force_bytes, string_types
from coreapi.exceptions import ParseError
from coreapi.schemas import JSONSchema
import collections
import json


def decode(struct):
    types = get_types(struct)
    if is_any(types, struct):
        return typesys.Any()

    allow_null = False
    if 'null' in types:
        allow_null = True
        types.remove('null')

    if len(types) == 1:
        return load_type(types.pop(), struct, allow_null)
    else:
        items = [load_type(typename, struct, False) for typename in types]
        return typesys.Union(items=items, allow_null=allow_null)


def get_types(struct):
    """
    Return the valid schema types as a set.
    """
    types = struct.get('type', [])
    if isinstance(types, string_types):
        types = set([types])
    else:
        types = set(types)

    if not types:
        types = set(['null', 'boolean', 'object', 'array', 'number', 'string'])

    if 'integer' in types and 'number' in types:
        types.remove('integer')

    return types


def is_any(types, struct):
    """
    Return true if all types are valid, and there are no type constraints.
    """
    ALL_PROPERTY_NAMES = set([
        'exclusiveMaximum', 'format', 'minItems', 'pattern', 'required',
        'multipleOf', 'maximum', 'minimum', 'maxItems', 'minLength',
        'uniqueItems', 'additionalItems', 'maxLength', 'items',
        'exclusiveMinimum', 'properties', 'additionalProperties',
        'minProperties', 'maxProperties', 'patternProperties'
    ])
    return len(types) == 6 and not set(struct.keys()) & ALL_PROPERTY_NAMES


def load_type(typename, struct, allow_null):
    attrs = {'allow_null': True} if allow_null else {}

    if typename == 'string':
        if 'minLength' in struct:
            attrs['min_length'] = struct['minLength']
        if 'maxLength' in struct:
            attrs['max_length'] = struct['maxLength']
        if 'pattern' in struct:
            attrs['pattern'] = struct['pattern']
        if 'format' in struct:
            attrs['format'] = struct['format']
        return typesys.String(**attrs)

    if typename in ['number', 'integer']:
        if 'minimum' in struct:
            attrs['minimum'] = struct['minimum']
        if 'maximum' in struct:
            attrs['maximum'] = struct['maximum']
        if 'exclusiveMinimum' in struct:
            attrs['exclusive_minimum'] = struct['exclusiveMinimum']
        if 'exclusiveMaximum' in struct:
            attrs['exclusive_maximum'] = struct['exclusiveMaximum']
        if 'multipleOf' in struct:
            attrs['multiple_of'] = struct['multipleOf']
        if 'format' in struct:
            attrs['format'] = struct['format']
        if typename == 'integer':
            return typesys.Integer(**attrs)
        return typesys.Number(**attrs)

    if typename == 'boolean':
        return typesys.Boolean(**attrs)

    if typename == 'object':
        if 'properties' in struct:
            attrs['properties'] = {
                key: decode(value)
                for key, value in struct['properties'].items()
            }
        if 'required' in struct:
            attrs['required'] = struct['required']
        if 'minProperties' in struct:
            attrs['min_properties'] = struct['minProperties']
        if 'maxProperties' in struct:
            attrs['max_properties'] = struct['maxProperties']
        if 'required' in struct:
            attrs['required'] = struct['required']
        if 'patternProperties' in struct:
            attrs['pattern_properties'] = {
                key: decode(value)
                for key, value in struct['patternProperties'].items()
            }
        if 'additionalProperties' in struct:
            if isinstance(struct['additionalProperties'], bool):
                attrs['additional_properties'] = struct['additionalProperties']
            else:
                attrs['additional_properties'] = decode(struct['additionalProperties'])
        return typesys.Object(**attrs)

    if typename == 'array':
        if 'items' in struct:
            if isinstance(struct['items'], list):
                attrs['items'] = [decode(item) for item in struct['items']]
            else:
                attrs['items'] = decode(struct['items'])
        if 'additionalItems' in struct:
            if isinstance(struct['additionalItems'], bool):
                attrs['additional_items'] = struct['additionalItems']
            else:
                attrs['additional_items'] = decode(struct['additionalItems'])
        if 'minItems' in struct:
            attrs['min_items'] = struct['minItems']
        if 'maxItems' in struct:
            attrs['max_items'] = struct['maxItems']
        if 'uniqueItems' in struct:
            attrs['unique_items'] = struct['uniqueItems']
        return typesys.Array(**attrs)

    assert False


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
        return decode(jsonschema)

    def decode_from_data_structure(self, struct):
        return decode(struct)

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

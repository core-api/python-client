from coreapi import typesys
from coreapi.compat import dict_type


class JSONSchema(typesys.Object):
    properties = dict_type([
        ('$ref', typesys.string()),
        ('type', typesys.string()),
        ('enum', typesys.Any),

        # String
        ('minLength', typesys.integer(minimum=0, default=0)),
        ('maxLength', typesys.integer(minimum=0)),
        ('pattern', typesys.string(format='regex')),
        ('format', typesys.string()),

        # Numeric
        ('minimum', typesys.number()),
        ('maximum', typesys.number()),
        ('exclusiveMinimum', typesys.boolean(default=False)),
        ('exclusiveMaximum', typesys.boolean(default=False)),
        ('multipleOf', typesys.number(minimum=0.0, exclusive_minimum=True)),

        # Object
        ('properties', typesys.obj()),  # TODO: typesys.ref('JSONSchema'),
        ('required', typesys.array(items=typesys.string(), min_items=1, unique=True)),

        # Array
        ('items', typesys.obj()),  # TODO: typesys.ref('JSONSchema'),
        ('additionalItems', typesys.boolean()),
        ('minItems', typesys.integer(minimum=0)),
        ('maxItems', typesys.integer(minimum=0)),
        ('uniqueItems', typesys.boolean()),
    ])

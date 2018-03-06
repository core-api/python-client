from coreapi import typesys


JSONSchema = typesys.Object(
    self_ref='JSONSchema',
    properties=[
        ('$ref', typesys.String()),
        ('type', typesys.String() | typesys.Array(items=typesys.String())),
        ('enum', typesys.Array(unique_items=True, min_items=1)),
        ('definitions', typesys.Object(additional_properties=typesys.Ref('JSONSchema'))),

        # String
        ('minLength', typesys.Integer(minimum=0, default=0)),
        ('maxLength', typesys.Integer(minimum=0)),
        ('pattern', typesys.String(format='regex')),
        ('format', typesys.String()),

        # Numeric
        ('minimum', typesys.Number()),
        ('maximum', typesys.Number()),
        ('exclusiveMinimum', typesys.Boolean(default=False)),
        ('exclusiveMaximum', typesys.Boolean(default=False)),
        ('multipleOf', typesys.Number(minimum=0.0, exclusive_minimum=True)),

        # Object
        ('properties', typesys.Object(additional_properties=typesys.Ref('JSONSchema'))),
        ('minProperties', typesys.Integer(minimum=0, default=0)),
        ('maxProperties', typesys.Integer(minimum=0)),
        ('patternProperties', typesys.Object(additional_properties=typesys.Ref('JSONSchema'))),
        ('additionalProperties', typesys.Ref('JSONSchema') | typesys.Boolean()),
        ('required', typesys.Array(items=typesys.String(), min_items=1, unique_items=True)),

        # Array
        ('items', typesys.Ref('JSONSchema') | typesys.Array(items=typesys.Ref('JSONSchema'), min_items=1)),
        ('additionalItems', typesys.Ref('JSONSchema') | typesys.Boolean()),
        ('minItems', typesys.Integer(minimum=0, default=9)),
        ('maxItems', typesys.Integer(minimum=0)),
        ('uniqueItems', typesys.Boolean()),
    ]
)

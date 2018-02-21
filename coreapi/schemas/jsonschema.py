from coreapi import typesys


JSONSchema = typesys.Object(
    properties=[
        ('$ref', typesys.String()),
        ('type', typesys.String()),
        ('enum', typesys.Any()),

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
        ('properties', typesys.Object()),  # TODO: typesys.ref('JSONSchema'),
        ('required', typesys.Array(items=typesys.String(), min_items=1, unique_items=True)),

        # Array
        ('items', typesys.Object()),  # TODO: typesys.ref('JSONSchema'),
        ('additionalItems', typesys.Boolean()),
        ('minItems', typesys.Integer(minimum=0)),
        ('maxItems', typesys.Integer(minimum=0)),
        ('uniqueItems', typesys.Boolean()),
    ]
)

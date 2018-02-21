from coreapi.compat import dict_type, string_types
import re


# TODO: Error on unknown attributes
# TODO: allow_blank?
# TODO: format (check type at start and allow, coerce, .native)
# TODO: default=empty
# TODO: check 'required' exists in 'properties'
# TODO: smarter ordering
# TODO: extra_properties=False by default
# TODO: inf, -inf, nan
# TODO: Overriding errors
# TODO: Blank booleans as False?


class ValidationError(Exception):
    def __init__(self, detail):
        assert isinstance(detail, (string_types, dict))
        self.detail = detail
        super(ValidationError, self).__init__(detail)


class NoDefault(object):
    pass


class Validator(object):
    errors = {}

    def __init__(self, title='', description='', default=NoDefault, definitions=None):
        definitions = {} if (definitions is None) else dict_type(definitions)

        assert isinstance(title, string_types)
        assert isinstance(description, string_types)
        assert all(isinstance(k, string_types) for k in definitions.keys())
        assert all(isinstance(v, Validator) for v in definitions.values())

        self.title = title
        self.description = description
        self.default = default
        self.definitions = definitions

    def validate(value, definitions=None):
        raise NotImplementedError()

    def error(self, code):
        message = self.error_message(code)
        raise ValidationError(message)

    def error_message(self, code):
        return self.errors[code].format(**self.__dict__)

    def has_default(self):
        return self.default is not NoDefault


class String(Validator):
    errors = {
        'type': 'Must be a string.',
        'blank': 'Must not be blank.',
        'max_length': 'Must have no more than {max_length} characters.',
        'min_length': 'Must have at least {min_length} characters.',
        'pattern': 'Must match the pattern /{pattern}/.',
        'format': 'Must be a valid {format}.',
        'enum': 'Must be a valid choice.',
        'exact': 'Must be {exact}.'
    }

    def __init__(self, max_length=None, min_length=None, pattern=None, enum=None, format=None, **kwargs):
        super(String, self).__init__(**kwargs)

        assert max_length is None or isinstance(max_length, int)
        assert min_length is None or isinstance(min_length, int)
        assert pattern is None or isinstance(pattern, string_types)
        assert enum is None or isinstance(enum, list) and all([isinstance(i, string_types) for i in enum])
        assert format is None or isinstance(format, string_types)

        self.max_length = max_length
        self.min_length = min_length
        self.pattern = pattern
        self.enum = enum
        self.format = format

    def validate(self, value, definitions=None):
        value = str(value)

        if self.enum is not None:
            if value not in self.enum:
                if len(self.enum) == 1:
                    self.error('exact')
                self.error('enum')

        if self.min_length is not None:
            if len(value) < self.min_length:
                if self.min_length == 1:
                    self.error('blank')
                else:
                    self.error('min_length')

        if self.max_length is not None:
            if len(value) > self.max_length:
                self.error('max_length')

        if self.pattern is not None:
            if not re.search(self.pattern, value):
                self.error('pattern')

        return value


class NumericType(Validator):
    """
    Base class for both `Number` and `Integer`.
    """
    numeric_type = None  # type: type
    errors = {
        'type': 'Must be a valid number.',
        'minimum': 'Must be greater than or equal to {minimum}.',
        'exclusive_minimum': 'Must be greater than {minimum}.',
        'maximum': 'Must be less than or equal to {maximum}.',
        'exclusive_maximum': 'Must be less than {maximum}.',
        'multiple_of': 'Must be a multiple of {multiple_of}.',
    }

    def __init__(self, minimum=None, maximum=None, exclusive_minimum=False, exclusive_maximum=False, multiple_of=None, enum=None, format=None, **kwargs):
        super(NumericType, self).__init__(**kwargs)

        assert minimum is None or isinstance(minimum, self.numeric_type)
        assert maximum is None or isinstance(maximum, self.numeric_type)
        assert isinstance(exclusive_minimum, bool)
        assert isinstance(exclusive_maximum, bool)
        assert multiple_of is None or isinstance(multiple_of, self.numeric_type)
        assert enum is None or isinstance(enum, list) and all([isinstance(i, string_types) for i in enum])
        assert format is None or isinstance(format, string_types)

        self.minimum = minimum
        self.maximum = maximum
        self.exclusive_minimum = exclusive_minimum
        self.exclusive_maximum = exclusive_maximum
        self.multiple_of = multiple_of
        self.enum = enum
        self.format = format

    def validate(self, value, definitions=None):
        try:
            value = self.numeric_type(value)
        except (TypeError, ValueError):
            self.error('type')

        if self.enum is not None:
            if value not in self.enum:
                if len(self.enum) == 1:
                    self.error('exact')
                self.error('enum')

        if self.minimum is not None:
            if self.exclusive_minimum:
                if value <= self.minimum:
                    self.error('exclusive_minimum')
            else:
                if value < self.minimum:
                    self.error('minimum')

        if self.maximum is not None:
            if self.exclusive_maximum:
                if value >= self.maximum:
                    self.error('exclusive_maximum')
            else:
                if value > self.maximum:
                    self.error('maximum')

        if self.multiple_of is not None:
            if isinstance(self.multiple_of, float):
                if not (value * (1 / self.multiple_of)).is_integer():
                    self.error('multiple_of')
            else:
                if value % self.multiple_of:
                    self.error('multiple_of')

        return value


class Number(NumericType):
    numeric_type = float


class Integer(NumericType):
    numeric_type = int


class Boolean(Validator):
    errors = {
        'type': 'Must be a valid boolean.'
    }

    def validate(self, value, definitions=None):
        if isinstance(value, (int, float, bool)):
            return bool(value)
        elif isinstance(value, str):
            try:
                return {
                    'true': True,
                    'false': False,
                    '1': True,
                    '0': False
                }[value.lower()]
            except KeyError:
                pass
        self.error('type')


class Object(Validator):
    errors = {
        'type': 'Must be an object.',
        'invalid_key': 'Object keys must be strings.',
        'required': 'This field is required.',
    }

    def __init__(self, properties=None, pattern_properties=None, additional_properties=None, required=None, **kwargs):
        super(Object, self).__init__(**kwargs)

        properties = {} if (properties is None) else dict_type(properties)
        pattern_properties = {} if (pattern_properties is None) else dict_type(pattern_properties)
        required = list(required) if isinstance(required, (list, tuple)) else required
        required = [] if (required is None) else required

        assert all(isinstance(k, string_types) for k in properties.keys())
        assert all(isinstance(v, Validator) for v in properties.values())
        assert all(isinstance(k, string_types) for k in pattern_properties.keys())
        assert all(isinstance(v, Validator) for v in pattern_properties.values())

        self.properties = properties
        self.pattern_properties = pattern_properties
        self.additional_properties = additional_properties
        self.required = required

    def validate(self, value, definitions=None):
        if definitions is None:
            definitions = dict(self.definitions)
            definitions[''] = self

        validated = dict_type()
        try:
            value = dict_type(value)
        except TypeError:
            self.error('type')

        # Ensure all property keys are strings.
        errors = {}
        if any(not isinstance(key, string_types) for key in value.keys()):
            self.error('invalid_key')

        # Properties
        for key, child_schema in self.properties.items():
            try:
                item = value.pop(key)
            except KeyError:
                if key in self.required:
                    errors[key] = self.error_message('required')
            else:
                try:
                    validated[key] = child_schema.validate(item, definitions=definitions)
                except ValidationError as exc:
                    errors[key] = exc.detail

        # Pattern properties
        if self.pattern_properties:
            for key in list(value.keys()):
                for pattern, child_schema in self.pattern_properties.items():
                    if re.search(pattern, key):
                        item = value.pop(key)
                        try:
                            validated[key] = child_schema.validate(item, definitions=definitions)
                        except ValidationError as exc:
                            errors[key] = exc.detail

        # Additional properties
        if self.additional_properties is not None:
            child_schema = self.additional_properties
            for key in list(value.keys()):
                item = value.pop(key)
                try:
                    validated[key] = child_schema.validate(item, definitions=definitions)
                except ValidationError as exc:
                    errors[key] = exc.detail

        if errors:
            raise ValidationError(errors)

        return validated


class Array(Validator):
    errors = {
        'type': 'Must be a list.',
        'min_items': 'Not enough items.',
        'max_items': 'Too many items.',
        'unique_items': 'This item is not unique.',
    }

    def __init__(self, items=None, additional_items=None, min_items=None, max_items=None, unique_items=False, **kwargs):
        super(Array, self).__init__(**kwargs)

        items = list(items) if isinstance(items, (list, tuple)) else items

        assert items is None or isinstance(items, Validator) or isinstance(items, list) and all(isinstance(i, Validator) for i in items)
        assert additional_items is None or isinstance(additional_items, (bool, Validator))
        assert min_items is None or isinstance(min_items, int)
        assert max_items is None or isinstance(max_items, int)
        assert isinstance(unique_items, bool)

        self.items = items
        self.additional_items = additional_items
        self.min_items = min_items
        self.max_items = max_items
        self.unique_items = unique_items

    def validate(self, value, definitions=None):
        if definitions is None:
            definitions = dict(self.definitions)
            definitions[''] = self

        validated = []
        try:
            value = list(value)
        except TypeError:
            self.error('type')

        if isinstance(self.items, list) and len(self.items) > 1:
            if len(value) < len(self.items):
                self.error('min_items')
            elif len(value) > len(self.items) and (self.additional_items is False):
                self.error('max_items')

        if self.min_items is not None and len(value) < self.min_items:
            self.error('min_items')
        elif self.max_items is not None and len(value) > self.max_items:
            self.error('max_items')

        # Ensure all items are of the right type.
        errors = {}
        if self.unique_items:
            seen_items = set()

        for pos, item in enumerate(value):
            try:
                if isinstance(self.items, list):
                    if pos < len(self.items):
                        item = self.items[pos].validate(item, definitions=definitions)
                    elif isinstance(self.additional_items, Validator):
                        item = self.additional_items.validate(item, definitions=definitions)
                elif self.items is not None:
                    item = self.items.validate(item, definitions=definitions)

                if self.unique_items:
                    if item in seen_items:
                        self.error('unique_items')
                    else:
                        seen_items.add(item)

                validated.append(item)
            except ValidationError as exc:
                errors[pos] = exc.detail

        if errors:
            raise ValidationError(errors)

        return validated


class Any(Validator):
    def validate(self, value, definitions=None):
        # TODO: Validate value matches primitive types
        return value


class Ref(Validator):
    def __init__(self, ref='', **kwargs):
        super(Ref, self).__init__(**kwargs)
        assert isinstance(ref, string_types)
        self.ref = ref

    def validate(self, value, definitions=None):
        assert definitions is not None, 'Ref.validate() requires definitions'
        assert self.ref in definitions, 'Ref "%s" not in definitions' % self.ref

        child_schema = definitions[self.ref]
        return child_schema.validate(value, definitions=definitions)

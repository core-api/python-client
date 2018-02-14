import re
# from typing import Any, Dict, List, Optional, Tuple, Union, overload  # noqa


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
        self.detail = detail
        super(ValidationError, self).__init__(detail)


class String(str):
    errors = {
        'type': 'Must be a string.',
        'blank': 'Must not be blank.',
        'max_length': 'Must have no more than {max_length} characters.',
        'min_length': 'Must have at least {min_length} characters.',
        'pattern': 'Must match the pattern /{pattern}/.',
        'format': 'Must be a valid {format}.',
    }
    title = None  # type: str
    description = None  # type: str
    max_length = None  # type: int
    min_length = None  # type: int
    pattern = None  # type: str
    format = None  # type: Any
    trim_whitespace = True

    def __new__(cls, value):
        value = str.__new__(cls, value)

        if cls.trim_whitespace:
            value = value.strip()

        if cls.min_length is not None:
            if len(value) < cls.min_length:
                if cls.min_length == 1:
                    cls.error('blank')
                else:
                    cls.error('min_length')

        if cls.max_length is not None:
            if len(value) > cls.max_length:
                cls.error('max_length')

        if cls.pattern is not None:
            if not re.search(cls.pattern, value):
                cls.error('pattern')

        return value

    @classmethod
    def error(cls, code):
        message = cls.errors[code].format(**cls.__dict__)
        raise ValidationError(message)  # from None


class NumericType(object):
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
    title = None  # type: str
    description = None  # type: str
    minimum = None  # type: Union[float, int]
    maximum = None  # type: Union[float, int]
    exclusive_minimum = False
    exclusive_maximum = False
    multiple_of = None  # type: Union[float, int]

    def __new__(cls, value):
        try:
            value = cls.numeric_type.__new__(cls, value)
        except (TypeError, ValueError):
            cls.error('type')

        if cls.minimum is not None:
            if cls.exclusive_minimum:
                if value <= cls.minimum:
                    cls.error('exclusive_minimum')
            else:
                if value < cls.minimum:
                    cls.error('minimum')

        if cls.maximum is not None:
            if cls.exclusive_maximum:
                if value >= cls.maximum:
                    cls.error('exclusive_maximum')
            else:
                if value > cls.maximum:
                    cls.error('maximum')

        if cls.multiple_of is not None:
            if isinstance(cls.multiple_of, float):
                failed = not (value * (1 / cls.multiple_of)).is_integer()
            else:
                failed = value % cls.multiple_of
            if failed:
                cls.error('multiple_of')

        return value

    @classmethod
    def error(cls, code):
        message = cls.errors[code].format(**cls.__dict__)
        raise ValidationError(message)  # from None


class Number(NumericType, float):
    numeric_type = float


class Integer(NumericType, int):
    numeric_type = int


class Boolean(object):
    native_type = bool
    errors = {
        'type': 'Must be a valid boolean.'
    }
    title = None  # type: str
    description = None  # type: str

    def __new__(cls, value):
        if isinstance(value, str):
            try:
                return {
                    'true': True,
                    'false': False,
                    '1': True,
                    '0': False
                }[value.lower()]
            except KeyError:
                cls.error('type')
        return bool(value)

    @classmethod
    def error(cls, code):
        message = cls.errors[code].format(**cls.__dict__)
        raise ValidationError(message)  # from None


class Enum(str):
    errors = {
        'enum': 'Must be a valid choice.',
        'exact': 'Must be {exact}.'
    }
    title = None  # type: str
    description = None  # type: str
    enum = []  # type: List[str]

    def __new__(cls, value):
        if value not in cls.enum:
            if len(cls.enum) == 1:
                cls.error('exact')
            cls.error('enum')
        return value

    @classmethod
    def error(cls, code):
        message = cls.errors[code].format(**cls.__dict__)
        raise ValidationError(message)  # from None


class Object(dict):
    errors = {
        'type': 'Must be an object.',
        'invalid_key': 'Object keys must be strings.',
        'required': 'This field is required.',
    }
    title = None  # type: str
    description = None  # type: str
    properties = {}  # type: Dict[str, type]
    pattern_properties = None  # type: Dict[str, type]
    additional_properties = None  # type: type
    required = []

    def __init__(self, value):
        try:
            value = dict(value)
        except TypeError:
            self.error('type')

        # Ensure all property keys are strings.
        errors = {}
        if any(not isinstance(key, str) for key in value.keys()):
            self.error('invalid_key')

        # Properties
        for key, child_schema in self.properties.items():
            try:
                item = value.pop(key)
            except KeyError:
                if key in self.required:
                    errors[key] = self.error_message('required')
            else:
                # Coerce value into the given schema type if needed.
                if isinstance(item, child_schema):
                    self[key] = item
                else:
                    try:
                        self[key] = child_schema(item)
                    except ValidationError as exc:
                        errors[key] = exc.detail

        # Pattern properties
        if self.pattern_properties is not None:
            for key in list(value.keys()):
                for pattern, child_schema in self.pattern_properties.items():
                    if re.search(pattern, key):
                        item = value.pop(key)
                        try:
                            self[key] = child_schema(item)
                        except ValidationError as exc:
                            errors[key] = exc.detail

        # Additional properties
        if self.additional_properties is not None:
            child_schema = self.additional_properties
            for key in list(value.keys()):
                item = value.pop(key)
                try:
                    self[key] = child_schema(item)
                except ValidationError as exc:
                    errors[key] = exc.detail

        if errors:
            raise ValidationError(errors)

    def lookup(self, keys, default=None):
        try:
            item = self[keys[0]]
        except KeyError:
            return default

        if len(keys) == 1:
            return item
        return item.lookup(keys[1:], default)

    @classmethod
    def error(cls, code):
        message = cls.errors[code].format(**cls.__dict__)
        raise ValidationError(message)  # from None

    @classmethod
    def error_message(cls, code):
        return cls.errors[code].format(**cls.__dict__)


class Array(list):
    errors = {
        'type': 'Must be a list.',
        'min_items': 'Not enough items.',
        'max_items': 'Too many items.',
        'unique_items': 'This item is not unique.',
    }
    title = None  # type: str
    description = None  # type: str
    items = None  # type: Union[type, List[type]]
    additional_items = False  # type: bool
    min_items = None  # type: Optional[int]
    max_items = None  # type: Optional[int]
    unique_items = False  # type: bool

    def __init__(self, value):
        try:
            value = list(value)
        except TypeError:
            self.error('type')

        if isinstance(self.items, list) and len(self.items) > 1:
            if len(value) < len(self.items):
                self.error('min_items')
            elif len(value) > len(self.items) and not self.additional_items:
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
                        item = self.items[pos](item)
                elif self.items is not None:
                    item = self.items(item)

                if self.unique_items:
                    if item in seen_items:
                        self.error('unique_items')
                    else:
                        seen_items.add(item)

                self.append(item)
            except ValidationError as exc:
                errors[pos] = exc.detail

        if errors:
            raise ValidationError(errors)

    def lookup(self, keys, default=None):
        try:
            item = self[keys[0]]
        except (TypeError, IndexError):
            return default

        if len(keys) == 1:
            return item
        return item.lookup(keys[1:], default)

    @classmethod
    def error(cls, code):
        message = cls.errors[code].format(**cls.__dict__)
        raise ValidationError(message)  # from None


class Any(object):
    title = None  # type: str
    description = None  # type: str

    def __new__(self, value):
        return value


def string(**kwargs):
    return type('String', (String,), kwargs)


def integer(**kwargs):
    return type('Integer', (Integer,), kwargs)


def number(**kwargs):
    return type('Number', (Number,), kwargs)


def boolean(**kwargs):
    return type('Boolean', (Boolean,), kwargs)


def enum(**kwargs):
    return type('Enum', (Enum,), kwargs)


def array(**kwargs):
    return type('Array', (Array,), kwargs)


def obj(**kwargs):
    return type('Object', (Object,), kwargs)


# def ref(to=''):
#     return type('Ref', (Ref,), {'to': to})

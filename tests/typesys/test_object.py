from coreapi.typesys import Object, Integer, String, ValidationError
import pytest


def test_object_type():
    schema = Object()
    assert schema.validate({}) == {}
    assert schema.validate({'a': 1}) == {'a': 1}
    with pytest.raises(ValidationError) as exc:
        schema.validate(1)
    assert exc.value.detail == 'Must be an object.'


def test_object_keys():
    schema = Object()
    with pytest.raises(ValidationError) as exc:
        schema.validate({1: 1})
    assert exc.value.detail == 'Object keys must be strings.'


def test_object_properties():
    schema = Object(properties={'num': Integer()})
    with pytest.raises(ValidationError) as exc:
        schema.validate({'num': 'abc'})
    assert exc.value.detail == {'num': 'Must be a number.'}


def test_object_required():
    schema = Object(required=['name'])
    assert schema.validate({'name': 1}) == {'name': 1}
    with pytest.raises(ValidationError) as exc:
        schema.validate({})
    assert exc.value.detail == {'name': 'This field is required.'}


def test_object_max_properties():
    schema = Object(max_properties=2)
    assert schema.validate({'a': 1, 'b': 2}) == {'a': 1, 'b': 2}
    with pytest.raises(ValidationError) as exc:
        schema.validate({'a': 1, 'b': 2, 'c': 3})
    assert exc.value.detail == 'Must have no more than 2 properties.'


def test_object_min_properties():
    schema = Object(min_properties=2)
    assert schema.validate({'a': 1, 'b': 2}) == {'a': 1, 'b': 2}
    with pytest.raises(ValidationError) as exc:
        assert schema.validate({'a': 1})
    assert exc.value.detail == 'Must have at least 2 properties.'


def test_object_empty():
    schema = Object(min_properties=1)
    assert schema.validate({'a': 1}) == {'a': 1}
    with pytest.raises(ValidationError) as exc:
        schema.validate({})
    assert exc.value.detail == 'Must not be empty.'


def test_object_null():
    schema = Object(allow_null=True)
    assert schema.validate(None) is None

    schema = Object()
    with pytest.raises(ValidationError) as exc:
        schema.validate(None)
    assert exc.value.detail == 'May not be null.'


def test_object_pattern_properties():
    schema = Object(pattern_properties={'^x-': Integer()})
    assert schema.validate({'x-foo': 123}) == {'x-foo': 123}
    with pytest.raises(ValidationError) as exc:
        schema.validate({'x-foo': 'abc'})
    assert exc.value.detail == {'x-foo': 'Must be a number.'}


def test_object_additional_properties_as_boolean():
    schema = Object(properties={'a': String()}, additional_properties=False)
    assert schema.validate({'a': 'abc'}) == {'a': 'abc'}
    with pytest.raises(ValidationError) as exc:
        schema.validate({'b': 'abc'})
    assert exc.value.detail == {'b': 'Unknown properties are not allowed.'}


def test_object_additional_properties_as_schema():
    schema = Object(properties={'a': String()}, additional_properties=Integer())
    assert schema.validate({'a': 'abc'}) == {'a': 'abc'}
    with pytest.raises(ValidationError) as exc:
        schema.validate({'b': 'abc'})
    assert exc.value.detail == {'b': 'Must be a number.'}

from coreapi.typesys import Array, String, Integer, ValidationError
import pytest


def test_array_type():
    schema = Array()
    assert schema.validate([]) == []
    assert schema.validate(['a', 1]) == ['a', 1]
    with pytest.raises(ValidationError) as exc:
        schema.validate(1)
    assert exc.value.detail == 'Must be an array.'


def test_array_items():
    schema = Array(items=String())
    assert schema.validate([]) == []
    assert schema.validate(['a', 'b', 'c']) == ['a', 'b', 'c']
    with pytest.raises(ValidationError) as exc:
        schema.validate(['a', 'b', 123])
    assert exc.value.detail == {2: 'Must be a string.'}


def test_array_items_as_list():
    schema = Array(items=[String(), Integer()])
    assert schema.validate([]) == []
    assert schema.validate(['a', 123]) == ['a', 123]
    with pytest.raises(ValidationError) as exc:
        schema.validate(['a', 'b'])
    assert exc.value.detail == {1: 'Must be a number.'}


def test_array_max_items():
    schema = Array(max_items=2)
    assert schema.validate([1, 2]) == [1, 2]
    with pytest.raises(ValidationError) as exc:
        schema.validate([1, 2, 3])
    assert exc.value.detail == 'Must have no more than 2 items.'


def test_array_min_items():
    schema = Array(min_items=2)
    assert schema.validate([1, 2]) == [1, 2]
    with pytest.raises(ValidationError) as exc:
        schema.validate([1])
    assert exc.value.detail == 'Must have at least 2 items.'


def test_array_empty():
    schema = Array(min_items=1)
    assert schema.validate([1]) == [1]
    with pytest.raises(ValidationError) as exc:
        schema.validate([])
    assert exc.value.detail == 'Must not be empty.'


def test_array_unique_items():
    schema = Array(unique_items=True)
    assert schema.validate([1, 2, 3]) == [1, 2, 3]
    with pytest.raises(ValidationError) as exc:
        schema.validate([1, 2, 1])
    assert exc.value.detail == {2: 'This item is not unique.'}


def test_array_additional_items_disallowed():
    schema = Array(items=[String(), Integer()])
    assert schema.validate(['a', 123, True]) == ['a', 123, True]

    schema = Array(items=[String(), Integer()], additional_items=False)
    with pytest.raises(ValidationError) as exc:
        schema.validate(['a', 123, True])
    assert exc.value.detail == 'May not contain additional items.'

    schema = Array(items=[String(), Integer()], additional_items=Integer())
    with pytest.raises(ValidationError) as exc:
        schema.validate(['a', 123, 'c'])
    assert exc.value.detail == {2: 'Must be a number.'}

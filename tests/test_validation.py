from coreapi import Link, required
from coreapi.validation import validate_parameters
import datetime
import pytest


now = datetime.datetime.now()


@pytest.fixture
def link():
    return Link(
        url='/',
        action='post',
        fields=[required('required'), 'optional']
    )


def test_link_with_correct_parameters(link):
    validate_parameters(link, {'required': 123})
    validate_parameters(link, {'required': 123, 'optional': 456})


def test_link_missing_required_parameter(link):
    with pytest.raises(ValueError):
        validate_parameters(link, {'optional': 456})


def test_link_with_additional_parameter(link):
    validate_parameters(link, {'required': 123, 'unknown': 123})


# Test invalid parameter types.

def test_invalid_type(link):
    with pytest.raises(TypeError):
        validate_parameters(link, {'required': now})


def test_invalid_type_in_list(link):
    with pytest.raises(TypeError):
        validate_parameters(link, {'required': [now]})


def test_invalid_type_in_dict(link):
    with pytest.raises(TypeError):
        validate_parameters(link, {'required': {"a": now}})


def test_invalid_key_in_dict(link):
    with pytest.raises(TypeError):
        validate_parameters(link, {'required': {1: "a"}})


# Test valid parameter types.

def test_valid_type_in_list(link):
    validate_parameters(link, {'required': [123]})


def test_valid_type_in_dict(link):
    validate_parameters(link, {'required': {"a": 123}})

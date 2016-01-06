from coreapi import Link, required
from coreapi.validation import validate_parameters
import pytest


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


def test_link_with_invalid_parameter(link):
    with pytest.raises(ValueError):
        validate_parameters(link, {'required': 123, 'unknown': 123})

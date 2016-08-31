from coreapi import exceptions, utils
import datetime
import pytest


def test_validate_path_param():
    assert utils.validate_path_param(1, name='example') == '1'
    assert utils.validate_path_param(True, name='example') == 'true'
    with pytest.raises(exceptions.ValidationError):
        utils.validate_path_param(None, name='example')
    with pytest.raises(exceptions.ValidationError):
        utils.validate_path_param('', name='example')
    with pytest.raises(exceptions.ValidationError):
        utils.validate_path_param({}, name='example')
    with pytest.raises(exceptions.ValidationError):
        utils.validate_path_param([], name='example')


def test_validate_query_param():
    assert utils.validate_query_param(1, name='example') == '1'
    assert utils.validate_query_param(True, name='example') == 'true'
    assert utils.validate_query_param(None, name='example') == ''
    assert utils.validate_query_param('', name='example') == ''
    assert utils.validate_query_param([1, 2, 3], name='example') == ['1', '2', '3']
    with pytest.raises(exceptions.ValidationError):
        utils.validate_query_param({}, name='example')
    with pytest.raises(exceptions.ValidationError):
        utils.validate_query_param([1, 2, {}], name='example')


def test_validate_form_data():
    data = {
        'string': 'abc',
        'integer': 123,
        'number': 123.456,
        'boolean': True,
        'null': None,
        'array': [1, 2, 3],
        'object': {'a': 1, 'b': 2, 'c': 3}
    }
    assert utils.validate_form_data(data, 'application/json', name='example') == data
    with pytest.raises(exceptions.ValidationError):
        data = datetime.datetime.now()
        utils.validate_form_data(data, 'application/json', name='example')

    assert utils.validate_form_data(123, 'application/x-www-form-urlencoded', name='example') == '123'

    with pytest.raises(exceptions.InvalidLinkError):
        assert utils.validate_form_data(123, 'invalid/media-type', name='example')
    with pytest.raises(exceptions.InvalidLinkError):
        assert utils.validate_form_data(123, '', name='example')

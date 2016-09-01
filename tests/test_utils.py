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
    # Valid JSON
    data = {
        'string': 'abc',
        'integer': 123,
        'number': 123.456,
        'boolean': True,
        'null': None,
        'array': [1, 2, 3],
        'object': {'a': 1, 'b': 2, 'c': 3}
    }
    assert utils.validate_form_param(data, 'application/json', name='example') == data
    assert utils.validate_body_param(data, 'application/json', name='example') == data

    # Invalid JSON
    data = datetime.datetime.now()
    with pytest.raises(exceptions.ValidationError):
        utils.validate_form_param(data, 'application/json', name='example')
    with pytest.raises(exceptions.ValidationError):
        utils.validate_body_param(data, 'application/json', name='example')

    # URL Encoded
    assert utils.validate_form_param(123, 'application/x-www-form-urlencoded', name='example') == '123'
    assert utils.validate_body_param({'a': 123}, 'application/x-www-form-urlencoded', name='example') == {'a': '123'}
    with pytest.raises(exceptions.ValidationError):
        utils.validate_form_param({'a': {'foo': 'bar'}}, 'application/x-www-form-urlencoded', name='example')
    with pytest.raises(exceptions.ValidationError):
        utils.validate_body_param(123, 'application/x-www-form-urlencoded', name='example')

    # Multipart
    assert utils.validate_form_param(123, 'multipart/form', name='example') == '123'
    assert utils.validate_body_param({'a': 123}, 'multipart/form', name='example') == {'a': '123'}
    with pytest.raises(exceptions.ValidationError):
        utils.validate_form_param({'a': {'foo': 'bar'}}, 'multipart/form', name='example')
    with pytest.raises(exceptions.ValidationError):
        utils.validate_body_param(123, 'multipart/form', name='example')

    # Raw upload
    with pytest.raises(exceptions.ValidationError):
        utils.validate_body_param(123, 'application/octet-stream', name='example')

    # Invalid encoding on outgoing request
    with pytest.raises(exceptions.TransportError):
        assert utils.validate_form_param(123, 'invalid/media-type', name='example')
    with pytest.raises(exceptions.TransportError):
        assert utils.validate_form_param(123, '', name='example')
    with pytest.raises(exceptions.TransportError):
        assert utils.validate_body_param(123, 'invalid/media-type', name='example')

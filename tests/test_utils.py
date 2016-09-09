from coreapi import exceptions, utils
import datetime
import pytest


def test_validate_path_param():
    assert utils.validate_path_param(1) == '1'
    assert utils.validate_path_param(True) == 'true'
    with pytest.raises(exceptions.ValidationError):
        utils.validate_path_param(None)
    with pytest.raises(exceptions.ValidationError):
        utils.validate_path_param('')
    with pytest.raises(exceptions.ValidationError):
        utils.validate_path_param({})
    with pytest.raises(exceptions.ValidationError):
        utils.validate_path_param([])


def test_validate_query_param():
    assert utils.validate_query_param(1) == '1'
    assert utils.validate_query_param(True) == 'true'
    assert utils.validate_query_param(None) == ''
    assert utils.validate_query_param('') == ''
    assert utils.validate_query_param([1, 2, 3]) == ['1', '2', '3']
    with pytest.raises(exceptions.ValidationError):
        utils.validate_query_param({})
    with pytest.raises(exceptions.ValidationError):
        utils.validate_query_param([1, 2, {}])


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
    assert utils.validate_form_param(data, 'application/json') == data
    assert utils.validate_body_param(data, 'application/json') == data

    # Invalid JSON
    data = datetime.datetime.now()
    with pytest.raises(exceptions.ValidationError):
        utils.validate_form_param(data, 'application/json')
    with pytest.raises(exceptions.ValidationError):
        utils.validate_body_param(data, 'application/json')

    data = utils.File('abc.txt', None)
    with pytest.raises(exceptions.ValidationError):
        utils.validate_form_param(data, 'application/json')
    with pytest.raises(exceptions.ValidationError):
        utils.validate_body_param(data, 'application/json')

    # URL Encoded
    assert utils.validate_form_param(123, 'application/x-www-form-urlencoded') == '123'
    assert utils.validate_body_param({'a': 123}, 'application/x-www-form-urlencoded') == {'a': '123'}
    with pytest.raises(exceptions.ValidationError):
        utils.validate_form_param({'a': {'foo': 'bar'}}, 'application/x-www-form-urlencoded')
    with pytest.raises(exceptions.ValidationError):
        utils.validate_body_param(123, 'application/x-www-form-urlencoded')
    with pytest.raises(exceptions.ValidationError):
        utils.validate_form_param(utils.File('abc.txt', None), 'application/x-www-form-urlencoded')
    with pytest.raises(exceptions.ValidationError):
        utils.validate_body_param({'a': utils.File('abc.txt', None)}, 'application/x-www-form-urlencoded')

    # Multipart
    assert utils.validate_form_param(123, 'multipart/form-data') == '123'
    assert utils.validate_form_param(utils.File('abc.txt', None), 'multipart/form-data') == utils.File('abc.txt', None)
    assert utils.validate_body_param({'a': 123}, 'multipart/form-data') == {'a': '123'}
    assert utils.validate_body_param({'a': utils.File('abc.txt', None)}, 'multipart/form-data') == {'a': utils.File('abc.txt', None)}
    with pytest.raises(exceptions.ValidationError):
        utils.validate_form_param({'a': {'foo': 'bar'}}, 'multipart/form-data')
    with pytest.raises(exceptions.ValidationError):
        utils.validate_body_param(123, 'multipart/form-data')

    # Raw upload
    with pytest.raises(exceptions.ValidationError):
        utils.validate_body_param(123, 'application/octet-stream')

    # Invalid encoding on outgoing request
    with pytest.raises(exceptions.NetworkError):
        assert utils.validate_form_param(123, 'invalid/media-type')
    with pytest.raises(exceptions.NetworkError):
        assert utils.validate_form_param(123, '')
    with pytest.raises(exceptions.NetworkError):
        assert utils.validate_body_param(123, 'invalid/media-type')

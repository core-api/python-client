# coding: utf-8
from coreapi import Client
from coreapi import Array, Document, Object, Link, Error, Field
from coreapi.exceptions import LinkLookupError
import pytest


@pytest.fixture
def doc():
    return Document(
        url='http://example.org',
        title='Example',
        content={
            'integer': 123,
            'dict': {'key': 'value'},
            'list': [1, 2, 3],
            'link': Link(
                url='/',
                action='post',
                transform='inplace',
                fields=['optional', Field('required', required=True, location='path')]
            ),
            'nested': {'child': Link(url='/123')}
        })


@pytest.fixture
def obj():
    return Object({'key': 'value', 'nested': {'abc': 123}})


@pytest.fixture
def array():
    return Array([{'a': 1}, {'b': 2}, {'c': 3}])


@pytest.fixture
def link():
    return Link(
        url='/',
        action='post',
        fields=[Field('required', required=True), 'optional']
    )


@pytest.fixture
def error():
    return Error(title='', content={'messages': ['failed']})


def _dedent(string):
    """
    Convenience function for dedenting multiline strings,
    for string comparison purposes.
    """
    lines = string.splitlines()
    if not lines[0].strip():
        lines = lines[1:]
    if not lines[-1].strip():
        lines = lines[:-1]
    leading_spaces = len(lines[0]) - len(lines[0].lstrip(' '))
    return '\n'.join(line[leading_spaces:] for line in lines)


# Documents are immutable.

def test_document_does_not_support_key_assignment(doc):
    with pytest.raises(TypeError):
        doc['integer'] = 456


def test_document_does_not_support_property_assignment(doc):
    with pytest.raises(TypeError):
        doc.integer = 456


def test_document_does_not_support_key_deletion(doc):
    with pytest.raises(TypeError):
        del doc['integer']


# Objects are immutable.

def test_object_does_not_support_key_assignment(obj):
    with pytest.raises(TypeError):
        obj['key'] = 456


def test_object_does_not_support_property_assignment(obj):
    with pytest.raises(TypeError):
        obj.integer = 456


def test_object_does_not_support_key_deletion(obj):
    with pytest.raises(TypeError):
        del obj['key']


# Arrays are immutable.

def test_array_does_not_support_item_assignment(array):
    with pytest.raises(TypeError):
        array[1] = 456


def test_array_does_not_support_property_assignment(array):
    with pytest.raises(TypeError):
        array.integer = 456


def test_array_does_not_support_item_deletion(array):
    with pytest.raises(TypeError):
        del array[1]


# Links are immutable.

def test_link_does_not_support_property_assignment():
    link = Link()
    with pytest.raises(TypeError):
        link.integer = 456


# Errors are immutable.

def test_error_does_not_support_property_assignment():
    error = Error(content={'messages': ['failed']})
    with pytest.raises(TypeError):
        error.integer = 456


# Children in documents are immutable primitives.

def test_document_dictionaries_coerced_to_objects(doc):
    assert isinstance(doc['dict'], Object)


def test_document_lists_coerced_to_arrays(doc):
    assert isinstance(doc['list'], Array)


# The `delete` and `set` methods return new instances.

def test_document_delete(doc):
    new = doc.delete('integer')
    assert doc is not new
    assert set(new.keys()) == set(doc.keys()) - set(['integer'])
    for key in new.keys():
        assert doc[key] is new[key]


def test_document_set(doc):
    new = doc.set('integer', 456)
    assert doc is not new
    assert set(new.keys()) == set(doc.keys())
    for key in set(new.keys()) - set(['integer']):
        assert doc[key] is new[key]


def test_object_delete(obj):
    new = obj.delete('key')
    assert obj is not new
    assert set(new.keys()) == set(obj.keys()) - set(['key'])
    for key in new.keys():
        assert obj[key] is new[key]


def test_object_set(obj):
    new = obj.set('key', 456)
    assert obj is not new
    assert set(new.keys()) == set(obj.keys())
    for key in set(new.keys()) - set(['key']):
        assert obj[key] is new[key]


def test_array_delete(array):
    new = array.delete(1)
    assert array is not new
    assert len(new) == len(array) - 1
    assert new[0] is array[0]
    assert new[1] is array[2]


def test_array_set(array):
    new = array.set(1, 456)
    assert array is not new
    assert len(new) == len(array)
    assert new[0] is array[0]
    assert new[1] == 456
    assert new[2] is array[2]


# The `delete_in` and `set_in` functions return new instances.

def test_delete_in():
    nested = Object({'key': [{'abc': 123}, {'def': 456}], 'other': 0})

    assert nested.delete_in(['key', 0]) == {'key': [{'def': 456}], 'other': 0}
    assert nested.delete_in(['key']) == {'other': 0}
    assert nested.delete_in([]) is None


def test_set_in():
    nested = Object({'key': [{'abc': 123}, {'def': 456}], 'other': 0})
    insert = Object({'xyz': 789})

    assert (
        nested.set_in(['key', 0], insert) ==
        {'key': [{'xyz': 789}, {'def': 456}], 'other': 0}
    )
    assert (
        nested.set_in(['key'], insert) ==
        {'key': {'xyz': 789}, 'other': 0}
    )
    assert nested.set_in([], insert) == {'xyz': 789}


# Container types have a uniquely identifying representation.

def test_document_repr(doc):
    assert repr(doc) == (
        "Document(url='http://example.org', title='Example', content={"
        "'dict': {'key': 'value'}, "
        "'integer': 123, "
        "'list': [1, 2, 3], "
        "'nested': {'child': Link(url='/123')}, "
        "'link': Link(url='/', action='post', transform='inplace', "
        "fields=['optional', Field('required', required=True, location='path')])"
        "})"
    )
    assert eval(repr(doc)) == doc


def test_object_repr(obj):
    assert repr(obj) == "Object({'key': 'value', 'nested': {'abc': 123}})"
    assert eval(repr(obj)) == obj


def test_array_repr(array):
    assert repr(array) == "Array([{'a': 1}, {'b': 2}, {'c': 3}])"
    assert eval(repr(array)) == array


def test_link_repr(link):
    assert repr(link) == "Link(url='/', action='post', fields=[Field('required', required=True), 'optional'])"
    assert eval(repr(link)) == link


def test_error_repr(error):
    assert repr(error) == "Error(title='', content={'messages': ['failed']})"
    assert eval(repr(error)) == error


# Container types have a convenient string representation.

def test_document_str(doc):
    assert str(doc) == _dedent("""
        <Example "http://example.org">
            dict: {
                key: "value"
            }
            integer: 123
            list: [
                1,
                2,
                3
            ]
            nested: {
                child()
            }
            link(required, [optional])
    """)


def test_newline_str():
    doc = Document(content={'foo': '1\n2'})
    assert str(doc) == _dedent("""
        <Document "">
            foo: "1
                  2"
    """)


def test_object_str(obj):
    assert str(obj) == _dedent("""
        {
            key: "value"
            nested: {
                abc: 123
            }
        }
    """)


def test_array_str(array):
    assert str(array) == _dedent("""
        [
            {
                a: 1
            },
            {
                b: 2
            },
            {
                c: 3
            }
        ]
    """)


def test_link_str(link):
    assert str(link) == "link(required, [optional])"


def test_error_str(error):
    assert str(error) == _dedent("""
        <Error>
            messages: [
                "failed"
            ]
    """)


def test_document_urls():
    doc = Document(url='http://example.org/', title='Example', content={
        'a': Document(title='Full', url='http://example.com/123'),
        'b': Document(title='Path', url='http://example.org/123'),
        'c': Document(title='None', url='http://example.org/')
    })
    assert str(doc) == _dedent("""
        <Example "http://example.org/">
            a: <Full "http://example.com/123">
            b: <Path "http://example.org/123">
            c: <None "http://example.org/">
    """)


# Container types support equality functions.

def test_document_equality(doc):
    assert doc == {
        'integer': 123,
        'dict': {'key': 'value'},
        'list': [1, 2, 3],
        'link': Link(
            url='/',
            action='post',
            transform='inplace',
            fields=['optional', Field('required', required=True, location='path')]
        ),
        'nested': {'child': Link(url='/123')}
    }


def test_object_equality(obj):
    assert obj == {'key': 'value', 'nested': {'abc': 123}}


def test_array_equality(array):
    assert array == [{'a': 1}, {'b': 2}, {'c': 3}]


# Container types support len.

def test_document_len(doc):
    assert len(doc) == 5


def test_object_len(obj):
    assert len(obj) == 2


# Documents meet the Core API constraints.

def test_document_url_must_be_string():
    with pytest.raises(TypeError):
        Document(url=123)


def test_document_title_must_be_string():
    with pytest.raises(TypeError):
        Document(title=123)


def test_document_content_must_be_dict():
    with pytest.raises(TypeError):
        Document(content=123)


def test_document_keys_must_be_strings():
    with pytest.raises(TypeError):
        Document(content={0: 123})


def test_object_keys_must_be_strings():
    with pytest.raises(TypeError):
        Object(content={0: 123})


def test_error_title_must_be_string():
    with pytest.raises(TypeError):
        Error(title=123)


def test_error_content_must_be_dict():
    with pytest.raises(TypeError):
        Error(content=123)


def test_error_keys_must_be_strings():
    with pytest.raises(TypeError):
        Error(content={0: 123})


# Link arguments must be valid.

def test_link_url_must_be_string():
    with pytest.raises(TypeError):
        Link(url=123)


def test_link_action_must_be_string():
    with pytest.raises(TypeError):
        Link(action=123)


def test_link_transform_must_be_string():
    with pytest.raises(TypeError):
        Link(transform=123)


def test_link_fields_must_be_list():
    with pytest.raises(TypeError):
        Link(fields=123)


def test_link_field_items_must_be_valid():
    with pytest.raises(TypeError):
        Link(fields=[123])


# Invalid calls to '.action()' should error.

def test_keys_should_be_a_list_or_string(doc):
    client = Client()
    with pytest.raises(TypeError):
        client.action(doc, True)


def test_keys_should_be_a_list_of_strings_or_ints(doc):
    client = Client()
    with pytest.raises(TypeError):
        client.action(doc, ['nested', {}])


def test_keys_should_be_valid_indexes(doc):
    client = Client()
    with pytest.raises(LinkLookupError):
        client.action(doc, 'dummy')


def test_keys_should_access_a_link(doc):
    client = Client()
    with pytest.raises(LinkLookupError):
        client.action(doc, 'dict')


# Documents and Objects have `.data` and `.links` attributes

def test_document_data_and_links_properties():
    doc = Document(content={'a': 1, 'b': 2, 'c': Link(), 'd': Link()})
    assert sorted(list(doc.data.keys())) == ['a', 'b']
    assert sorted(list(doc.links.keys())) == ['c', 'd']


def test_object_data_and_links_properties():
    obj = Object({'a': 1, 'b': 2, 'c': Link(), 'd': Link()})
    assert sorted(list(obj.data.keys())) == ['a', 'b']
    assert sorted(list(obj.links.keys())) == ['c', 'd']

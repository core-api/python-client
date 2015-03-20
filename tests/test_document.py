# coding: utf-8
from coreapi import required, remove, replace, deep_remove, deep_replace
from coreapi import Array, Document, Object, Link
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
                trans='action',
                fields=['optional', required('required')]
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
        trans='action',
        fields=[required('required'), 'optional']
    )


def _dedent(string):
    """
    Convience function for dedenting multiline strings,
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


# Children in documents are immutable primatives.

def test_document_dictionaries_coerced_to_objects(doc):
    assert isinstance(doc['dict'], Object)


def test_document_lists_coerced_to_arrays(doc):
    assert isinstance(doc['list'], Array)


# The `remove` and `replace` functions return new instances.

def test_document_remove(doc):
    new = remove(doc, 'integer')
    assert doc is not new
    assert set(new.keys()) == set(doc.keys()) - set(['integer'])
    for key in new.keys():
        assert doc[key] is new[key]


def test_document_replace(doc):
    new = replace(doc, 'integer', 456)
    assert doc is not new
    assert set(new.keys()) == set(doc.keys())
    for key in set(new.keys()) - set(['integer']):
        assert doc[key] is new[key]


def test_object_remove(obj):
    new = remove(obj, 'key')
    assert obj is not new
    assert set(new.keys()) == set(obj.keys()) - set(['key'])
    for key in new.keys():
        assert obj[key] is new[key]


def test_object_replace(obj):
    new = replace(obj, 'key', 456)
    assert obj is not new
    assert set(new.keys()) == set(obj.keys())
    for key in set(new.keys()) - set(['key']):
        assert obj[key] is new[key]


def test_array_remove(array):
    new = remove(array, 1)
    assert array is not new
    assert len(new) == len(array) - 1
    assert new[0] is array[0]
    assert new[1] is array[2]


def test_array_replace(array):
    new = replace(array, 1, 456)
    assert array is not new
    assert len(new) == len(array)
    assert new[0] is array[0]
    assert new[1] == 456
    assert new[2] is array[2]


# The `deep_remove` and `deep_replace` functions return new instances.

def test_deep_remove():
    nested = Object({'key': [{'abc': 123}, {'def': 456}], 'other': 0})

    assert deep_remove(nested, ['key', 0]) == {'key': [{'def': 456}], 'other': 0}
    assert deep_remove(nested, ['key']) == {'other': 0}
    assert deep_remove(nested, []) is None


def test_deep_replace():
    nested = Object({'key': [{'abc': 123}, {'def': 456}], 'other': 0})
    insert = Object({'xyz': 789})

    assert (
        deep_replace(nested, ['key', 0], insert) ==
        {'key': [{'xyz': 789}, {'def': 456}], 'other': 0}
    )
    assert (
        deep_replace(nested, ['key'], insert) ==
        {'key': {'xyz': 789}, 'other': 0}
    )
    assert deep_replace(nested, [], insert) == {'xyz': 789}


# The `remove` and `replace` functions raise TypeError on incorrect types.

def test_remove_type_error():
    node = {'key': 'value'}
    with pytest.raises(TypeError):
        remove(node, 'key')


def test_replace_type_error():
    node = {'key': 'value'}
    with pytest.raises(TypeError):
        replace(node, 'key', 123)


def test_deep_remove_type_error():
    node = {'key': 'value'}
    with pytest.raises(TypeError):
        deep_remove(node, ['key'])


def test_deep_replace_type_error():
    node = {'key': 'value'}
    with pytest.raises(TypeError):
        deep_replace(node, ['key'], 123)


# Container types have a uniquely identifying representation.

def test_document_repr(doc):
    assert repr(doc) == (
        "Document(url='http://example.org', title='Example', content={"
        "'dict': {'key': 'value'}, "
        "'integer': 123, "
        "'list': [1, 2, 3], "
        "'nested': {'child': Link(url='/123')}, "
        "'link': Link(url='/', trans='action', "
        "fields=['optional', required('required')])"
        "})"
    )
    assert eval(repr(doc)) == doc


def test_object_repr(obj):
    assert repr(obj) == "Object({'key': 'value', 'nested': {'abc': 123}})"
    assert eval(repr(obj)) == obj


def test_array_repr(array):
    assert repr(array) == "Array([{'a': 1}, {'b': 2}, {'c': 3}])"
    assert eval(repr(array)) == array


# Container types have a convenient string representation.

def test_document_str(doc):
    assert str(doc) == _dedent("""
        <Example 'http://example.org'>
            'dict': {
                'key': 'value'
            },
            'integer': 123,
            'list': [
                1,
                2,
                3
            ],
            'nested': {
                'child': link()
            },
            'link': link(required, [optional])
    """)


def test_object_str(obj):
    assert str(obj) == _dedent("""
        {
            'key': 'value',
            'nested': {
                'abc': 123
            }
        }
    """)


def test_array_str(array):
    assert str(array) == _dedent("""
        [
            {
                'a': 1
            },
            {
                'b': 2
            },
            {
                'c': 3
            }
        ]
    """)


def test_link_str(link):
    assert str(link) == "link(required, [optional])"


# Container types support equality functions.

def test_document_equality(doc):
    assert doc == {
        'integer': 123,
        'dict': {'key': 'value'},
        'list': [1, 2, 3],
        'link': Link(
            url='/',
            trans='action',
            fields=['optional', required('required')]
        ),
        'nested': {'child': Link(url='/123')}
    }


def test_object_equality(obj):
    assert obj == {'key': 'value', 'nested': {'abc': 123}}


def test_array_equality(array):
    assert array == [{'a': 1}, {'b': 2}, {'c': 3}]


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


def test_document_values_must_be_valid_primatives():
    with pytest.raises(TypeError):
        Document(content={'a': set()})


def test_object_keys_must_be_strings():
    with pytest.raises(TypeError):
        Object(content={0: 123})


def test_array_may_not_contain_links():
    with pytest.raises(TypeError):
        Array([Link()])


# Link arguments must be valid.

def test_link_url_must_be_string():
    with pytest.raises(TypeError):
        Link(url=123)


def test_link_trans_must_be_string():
    with pytest.raises(TypeError):
        Link(trans=123)


def test_link_trans_must_be_valid():
    with pytest.raises(ValueError):
        Link(trans='fail')


def test_link_fields_must_be_list():
    with pytest.raises(TypeError):
        Link(fields=123)


def test_link_field_items_must_be_valid():
    with pytest.raises(TypeError):
        Link(fields=[123])


# Links correctly validate required and optional parameters.

def test_link_with_correct_parameters(link):
    link._validate(required=123)
    link._validate(required=123, optional=456)


def test_link_missing_required_parameter(link):
    with pytest.raises(ValueError):
        link._validate(optional=456)


def test_link_with_invalid_parameter(link):
    with pytest.raises(ValueError):
        link._validate(required=123, unknown=123)


# Invalid calls to '.action()' should error.

def test_keys_should_be_a_list(doc):
    with pytest.raises(TypeError):
        doc.action('nested')


def test_keys_should_be_a_list_of_strings_or_ints(doc):
    with pytest.raises(TypeError):
        doc.action(['nested', {}])


def test_keys_should_be_valid_indexes(doc):
    with pytest.raises(KeyError):
        doc.action(['dummy'])


def test_keys_should_access_a_link(doc):
    with pytest.raises(ValueError):
        doc.action(['dict'])

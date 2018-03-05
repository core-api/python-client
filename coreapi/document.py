# coding: utf-8
from __future__ import unicode_literals
from collections import Mapping, OrderedDict
from coreapi.compat import coreschema_to_typesys, string_types


def _to_objects(value):
    if isinstance(value, dict):
        return Object(value)
    return value


def _repr(node):
    from coreapi.codecs.python import PythonCodec
    return PythonCodec().encode(node)


def _str(node):
    from coreapi.codecs.display import DisplayCodec
    return DisplayCodec().encode(node)


def _key_sorting(item):
    """
    Document and Object sorting.
    Regular attributes sorted alphabetically.
    Links are sorted based on their URL and method.
    """
    key, value = item
    if isinstance(value, Link):
        method_priority = {
            'get': 0,
            'post': 1,
            'put': 2,
            'patch': 3,
            'delete': 4
        }.get(value.method, 5)
        return (1, (value.url, method_priority))
    return (0, key)


# The Core API primitives:

class Document(Mapping):
    """
    The Core API document type.

    Expresses the data that the client may access,
    and the actions that the client may perform.
    """
    def __init__(self, url=None, title=None, description=None, version=None, media_type=None, content=None, sections=None):
        content = {} if (content is None) else content

        if url is not None and not isinstance(url, string_types):
            raise TypeError("'url' must be a string.")
        if title is not None and not isinstance(title, string_types):
            raise TypeError("'title' must be a string.")
        if description is not None and not isinstance(description, string_types):
            raise TypeError("'description' must be a string.")
        if version is not None and not isinstance(version, string_types):
            raise TypeError("'version' must be a string.")
        if media_type is not None and not isinstance(media_type, string_types):
            raise TypeError("'media_type' must be a string.")
        if not isinstance(content, dict):
            raise TypeError("'content' must be a dict.")
        if any([not isinstance(key, string_types) for key in content.keys()]):
            raise TypeError('content keys must be strings.')

        self._url = '' if (url is None) else url
        self._title = '' if (title is None) else title
        self._description = '' if (description is None) else description
        self._version = '' if (version is None) else version
        self._media_type = '' if (media_type is None) else media_type

        if sections:
            for section in sections:
                if not section.id:
                    for link in section.links:
                        content[link.id] = link
                else:
                    content[section.id] = {}
                    for link in section.links:
                        content[section.id][link.id] = link
            self.sections = sections

        self._data = {key: _to_objects(value) for key, value in content.items()}

    def __iter__(self):
        items = sorted(self._data.items(), key=_key_sorting)
        return iter([key for key, value in items])

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __repr__(self):
        return _repr(self)

    def __str__(self):
        return _str(self)

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return (
                self.url == other.url and
                self.title == other.title and
                self._data == other._data
            )
        return super(Document, self).__eq__(other)

    @property
    def url(self):
        return self._url

    @property
    def title(self):
        return self._title

    @property
    def description(self):
        return self._description

    @property
    def version(self):
        return self._version

    @property
    def media_type(self):
        return self._media_type

    @property
    def data(self):
        return OrderedDict([
            (key, value) for key, value in self.items()
            if not isinstance(value, Link)
        ])

    @property
    def links(self):
        return OrderedDict([
            (key, value) for key, value in self.items()
            if isinstance(value, Link)
        ])


class Section(object):
    def __init__(self, id=None, title=None, description=None, links=None):
        self.id = id
        self.title = title
        self.description = description
        self.links = links


class Object(Mapping):
    """
    An immutable mapping of strings to values.
    """
    def __init__(self, *args, **kwargs):
        data = dict(*args, **kwargs)
        if any([not isinstance(key, string_types) for key in data.keys()]):
            raise TypeError('Object keys must be strings.')
        self._data = {key: _to_objects(value) for key, value in data.items()}

    def __iter__(self):
        items = sorted(self._data.items(), key=_key_sorting)
        return iter([key for key, value in items])

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __repr__(self):
        return _repr(self)

    def __str__(self):
        return _str(self)

    @property
    def data(self):
        return OrderedDict([
            (key, value) for key, value in self.items()
            if not isinstance(value, Link)
        ])

    @property
    def links(self):
        return OrderedDict([
            (key, value) for key, value in self.items()
            if isinstance(value, Link)
        ])


class Link(object):
    """
    Links represent the actions that a client may perform.
    """
    def __init__(self, url=None, method=None, encoding=None, title=None, description=None, fields=None, action=None, id=None):
        if action is not None:
            method = action  # Deprecated

        if (url is not None) and (not isinstance(url, string_types)):
            raise TypeError("Argument 'url' must be a string.")
        if (method is not None) and (not isinstance(method, string_types)):
            raise TypeError("Argument 'method' must be a string.")
        if (encoding is not None) and (not isinstance(encoding, string_types)):
            raise TypeError("Argument 'encoding' must be a string.")
        if (title is not None) and (not isinstance(title, string_types)):
            raise TypeError("Argument 'title' must be a string.")
        if (description is not None) and (not isinstance(description, string_types)):
            raise TypeError("Argument 'description' must be a string.")
        if (fields is not None) and (not isinstance(fields, (list, tuple))):
            raise TypeError("Argument 'fields' must be a list.")
        if (fields is not None) and any([
            not (isinstance(item, string_types) or isinstance(item, Field))
            for item in fields
        ]):
            raise TypeError("Argument 'fields' must be a list of strings or fields.")

        self.id = id
        self._url = '' if (url is None) else url
        self._method = '' if (method is None) else method
        self._encoding = '' if (encoding is None) else encoding
        self._title = '' if (title is None) else title
        self._description = '' if (description is None) else description
        self._fields = () if (fields is None) else tuple([
            item if isinstance(item, Field) else Field(item, required=False, location='')
            for item in fields
        ])

    @property
    def url(self):
        return self._url

    @property
    def method(self):
        return self._method

    @property
    def encoding(self):
        return self._encoding

    @property
    def title(self):
        return self._title

    @property
    def description(self):
        return self._description

    @property
    def fields(self):
        return self._fields

    @property
    def action(self):
        # Deprecated
        return self._method

    def __eq__(self, other):
        return (
            isinstance(other, Link) and
            self.url == other.url and
            self.method == other.method and
            self.encoding == other.encoding and
            self.description == other.description and
            sorted(self.fields, key=lambda f: f.name) == sorted(other.fields, key=lambda f: f.name)
        )

    def __repr__(self):
        return _repr(self)

    def __str__(self):
        return _str(self)


class Field(object):
    def __init__(self, name, title='', description='', required=False, location='', schema=None, example=None):
        self.name = name
        self.title = title
        self.description = description
        self.location = location
        self.required = required
        self.schema = coreschema_to_typesys(schema)
        self.example = example

    def __eq__(self, other):
        return (
            isinstance(other, Field) and
            self.name == other.name and
            self.required == other.required and
            self.location == other.location and
            self.description == other.description and
            self.schema.__class__ == other.schema.__class__ and
            self.example == other.example
        )


class Error(Mapping):
    def __init__(self, title=None, content=None):
        data = {} if (content is None) else content

        if title is not None and not isinstance(title, string_types):
            raise TypeError("'title' must be a string.")
        if content is not None and not isinstance(content, dict):
            raise TypeError("'content' must be a dict.")
        if any([not isinstance(key, string_types) for key in data.keys()]):
            raise TypeError('content keys must be strings.')

        self._title = '' if (title is None) else title
        self._data = {key: _to_objects(value) for key, value in data.items()}

    def __iter__(self):
        items = sorted(self._data.items(), key=_key_sorting)
        return iter([key for key, value in items])

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __repr__(self):
        return _repr(self)

    def __str__(self):
        return _str(self)

    def __eq__(self, other):
        return (
            isinstance(other, Error) and
            self.title == other.title and
            self._data == other._data
        )

    @property
    def title(self):
        return self._title

    def get_messages(self):
        messages = []
        for value in self.values():
            if isinstance(value, list):
                messages += [
                    item for item in value if isinstance(item, string_types)
                ]
            elif isinstance(value, string_types):
                messages += [value]
        return messages


class Array(object):
    def __init__(self):
        assert False, 'Array is deprecated'

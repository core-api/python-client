# coding: utf-8
from __future__ import unicode_literals
from collections import OrderedDict, namedtuple
from coreapi.compat import string_types
import itypes


def _to_immutable(value):
    if isinstance(value, dict):
        return Object(value)
    elif isinstance(value, list):
        return Array(value)
    return value


def _repr(node):
    from coreapi.codecs.python import PythonCodec
    return PythonCodec().dump(node)


def _str(node):
    from coreapi.codecs.plaintext import PlainTextCodec
    return PlainTextCodec().dump(node)


def _key_sorting(item):
    """
    Document and Object sorting.
    Regular attributes sorted alphabetically, then links sorted alphabetically.
    """
    key, value = item
    if isinstance(value, Link):
        return (1, key)
    return (0, key)


# The field class, as used by Link objects:

Field = namedtuple('Field', ['name', 'required'])


def required(name):
    return Field(name, required=True)


# The Core API primatives:

class Document(itypes.Dict):
    """
    The Core API document type.

    Expresses the data that the client may access,
    and the actions that the client may perform.
    """

    def __init__(self, url=None, title=None, content=None):
        if title is None and content is None and isinstance(url, dict):
            # If a single positional argument is set and is a dictionary,
            # treat it as the document content.
            content = url
            url = None

        data = {} if (content is None) else content

        if url is not None and not isinstance(url, string_types):
            raise TypeError("'url' must be a string.")
        if title is not None and not isinstance(title, string_types):
            raise TypeError("'title' must be a string.")
        if content is not None and not isinstance(content, dict):
            raise TypeError("'content' must be a dict.")
        if any([not isinstance(key, string_types) for key in data.keys()]):
            raise TypeError('Document keys must be strings.')
        if any([not isinstance(value, primative_types) for value in data.values()]):
            raise TypeError('Document values must be primatives.')

        self._url = '' if (url is None) else url
        self._title = '' if (title is None) else title
        self._data = {key: _to_immutable(value) for key, value in data.items()}

    def clone(self, data):
        return Document(self.url, self.title, data)

    def __iter__(self):
        items = sorted(self._data.items(), key=_key_sorting)
        return iter([key for key, value in items])

    def __repr__(self):
        return _repr(self)

    def __str__(self):
        return _str(self)

    @property
    def url(self):
        return self._url

    @property
    def title(self):
        return self._title

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


class Object(itypes.Dict):
    """
    An immutable mapping of strings to values.
    """
    def __init__(self, *args, **kwargs):
        data = dict(*args, **kwargs)
        if any([not isinstance(key, string_types) for key in data.keys()]):
            raise TypeError('Object keys must be strings.')
        self._data = {key: _to_immutable(value) for key, value in data.items()}

    def __iter__(self):
        items = sorted(self._data.items(), key=_key_sorting)
        return iter([key for key, value in items])

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


class Array(itypes.List):
    """
    An immutable list type container.
    """
    def __init__(self, *args):
        self._data = [_to_immutable(value) for value in list(*args)]

    def __repr__(self):
        return _repr(self)

    def __str__(self):
        return _str(self)


class Link(itypes.Object):
    """
    Links represent the actions that a client may perform.
    """
    def __init__(self, url=None, action=None, inplace=None, fields=None):
        if (url is not None) and (not isinstance(url, string_types)):
            raise TypeError("Argument 'url' must be a string.")
        if (action is not None) and (not isinstance(action, string_types)):
            raise TypeError("Argument 'action' must be a string.")
        if (inplace is not None) and (not isinstance(inplace, bool)):
            raise TypeError("Argument 'inplace' must be a boolean.")
        if (fields is not None) and (not isinstance(fields, list)):
            raise TypeError("Argument 'fields' must be a list.")
        if (fields is not None) and any([
            not (isinstance(item, string_types) or isinstance(item, Field))
            for item in fields
        ]):
            raise TypeError("Argument 'fields' must be a list of strings or fields.")

        self._url = '' if (url is None) else url
        self._action = '' if (action is None) else action
        self._inplace = inplace
        self._fields = () if (fields is None) else tuple([
            item if isinstance(item, Field) else Field(item, required=False)
            for item in fields
        ])

    @property
    def url(self):
        return self._url

    @property
    def action(self):
        return self._action

    @property
    def inplace(self):
        return self._inplace

    @property
    def fields(self):
        return self._fields

    def __eq__(self, other):
        return (
            isinstance(other, Link) and
            self.url == other.url and
            self.action == other.action and
            self.inplace == other.inplace and
            set(self.fields) == set(other.fields)
        )

    def __repr__(self):
        return _repr(self)

    def __str__(self):
        return _str(self)


class Error(itypes.Object):
    """
    Represents an error message or messages from a Core API interface.
    """
    def __init__(self, messages):
        if not isinstance(messages, (list, tuple)):
            raise TypeError("'messages' should be a list of strings.")
        if any([not isinstance(message, string_types) for message in messages]):
            raise TypeError("'messages' should be a list of strings.")

        self._messages = tuple(messages)

    @property
    def messages(self):
        return list(self._messages)

    def __eq__(self, other):
        if isinstance(other, Error):
            return self.messages == other.messages
        return self.messages == other

    def __repr__(self):
        return _repr(self)

    def __str__(self):
        return _str(self)


primative_types = string_types + (
    type(None), int, float, bool, list, dict,
    Document, Object, Array, Link
)

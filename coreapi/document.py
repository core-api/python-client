# coding: utf-8
from __future__ import unicode_literals
from collections import Mapping, Sequence, namedtuple
from coreapi.compat import string_types, urlparse
from coreapi.exceptions import ErrorMessage


_transition_types = ('follow', 'action', 'create', 'update', 'delete')
_default_transition_type = 'follow'


def _default_link_func(document, link, **parameters):
    """
    When calling a link the default behavior is to call through
    to the HTTP transport layer.
    """
    from coreapi.transport import transition
    return transition(link.url, link.trans, parameters=parameters)


def _make_immutable(value):
    """
    Coerce standard python container types into our immutable primatives.
    Used when instantiating documents.

    Eg. Document({"meta": {"title": ...}, "notes": [...]})

    Notice that in the above style the instantiation is written as
    regular Python dicts, lists, but once we have the object it
    will consist of immutable container types.
    """
    if isinstance(value, dict):
        return Object(value)
    elif isinstance(value, (list, tuple)):
        return Array(value)
    elif (
        value is None or
        isinstance(value, string_types) or
        isinstance(value, (int, float, bool, Document, Object, Array, Link))
    ):
        return value

    raise TypeError("Invalid type in document. Got '%s'." % type(value))


def _validate_parameter(value):
    """
    When calling a link parameters must be primatives or Document instances.
    """
    if isinstance(value, (dict)):
        if any([not isinstance(key, string_types) for key in value.keys()]):
            raise TypeError("Invalid parameter. Dictionary keys must be strings.")
        [_validate_parameter(item) for item in value.values()]
    elif isinstance(value, (list, tuple)):
        [_validate_parameter(item) for item in value]
    elif (
        value is None or
        isinstance(value, string_types) or
        isinstance(value, (int, float, bool))
    ):
        pass
    else:
        raise TypeError("Invalid parameter type. Got '%s'." % type(value))


def _key_sorting(item):
    """
    Document and Object sorting.
    Regular attributes sorted alphabetically, then links sorted alphabetically.
    """
    key, value = item
    if isinstance(value, Link):
        return (1, key)
    return (0, key)


def _graceful_relative_url(base_url, url):
    """
    Return a graceful link for a URL relative to a base URL.

    * If they are the same, return an empty string.
    * If the have the same scheme and hostname, return the path & query params.
    * Otherwise return the full URL.
    """
    if url == base_url:
        return ''
    base_prefix = '%s://%s' % urlparse.urlparse(base_url or '')[0:2]
    url_prefix = '%s://%s' % urlparse.urlparse(url or '')[0:2]
    if base_prefix == url_prefix and url_prefix != '://':
        return url[len(url_prefix):]
    return url


def _document_repr(node):
    """
    Return the representation of a Document or other primative
    in plain python style. Only the outermost element gets the
    class wrapper.
    """
    if isinstance(node, Document):
        content = ', '.join([
            '%s: %s' % (repr(key), _document_repr(value))
            for key, value in node.items()
        ])
        return 'Document(url=%s, title=%s, content={%s})' % (
            repr(node.url), repr(node.title), content
        )
    elif isinstance(node, Object):
        return '{%s}' % ', '.join([
            '%s: %s' % (repr(key), _document_repr(value))
            for key, value in node.items()
        ])
    elif isinstance(node, Array):
        return '[%s]' % ', '.join([
            _document_repr(value) for value in node
        ])
    return repr(node)


def _document_str(node, indent=0, base_url=None):
    """
    Return a verbose, indented representation of a Document or other primative.
    """
    if isinstance(node, Document):
        head_indent = '    ' * indent
        body_indent = '    ' * (indent + 1)

        body = ',\n'.join([
            body_indent + repr(key) + ': ' +
            _document_str(value, indent + 1, base_url=node.url)
            for key, value in node.items()
        ])

        url = _graceful_relative_url(base_url, node.url)
        head = '<%s%s>' % (
            node.title.strip() or 'Document',
            ' ' + repr(url) if url else ''
        )
        return head if (not body) else head + '\n' + body

    elif isinstance(node, Object):
        head_indent = '    ' * indent
        body_indent = '    ' * (indent + 1)

        body = ',\n'.join([
            body_indent + repr(key) + ': ' +
            _document_str(value, indent + 1, base_url=base_url)
            for key, value in node.items()
        ])

        return '{}' if (not body) else '{\n' + body + '\n' + head_indent + '}'

    elif isinstance(node, Array):
        head_indent = '    ' * indent
        body_indent = '    ' * (indent + 1)

        body = ',\n'.join([
            body_indent + _document_str(value, indent + 1, base_url=base_url)
            for value in node
        ])

        return '[]' if (not body) else '[\n' + body + '\n' + head_indent + ']'

    elif isinstance(node, Link):
        return 'link(%s)' % node._fields_as_string()

    return repr(node)


# The field class, as used by Link objects:

Field = namedtuple('Field', ['name', 'required'])


def required(name):
    return Field(name, required=True)


# Functions for returning a modified copy of an immutable primative:

def remove(node, key):
    """
    Return a new immutable container type, with the given key removed.
    """
    if isinstance(node, (Document, Object)):
        data = dict(node._data)
    elif isinstance(node, Array):
        data = list(node._data)
    else:
        raise TypeError(
            "Expected Core API container type. Got '%s'." % type(node)
        )

    data.pop(key)
    if isinstance(node, Document):
        return type(node)(url=node.url, title=node.title, content=data)
    return type(node)(data)


def replace(node, key, value):
    """
    Return a new immutable container type, with the given key removed.
    """
    if isinstance(node, (Document, Object)):
        data = dict(node)
    elif isinstance(node, Array):
        data = list(node)
    else:
        raise TypeError(
            "Expected Core API container type. Got '%s'." % type(node)
        )

    data[key] = value
    if isinstance(node, Document):
        return type(node)(url=node.url, title=node.title, content=data)
    return type(node)(data)


def deep_remove(node, keys):
    """
    Return a new immutable container type, with the given nested key removed.
    """
    if not isinstance(node, (Array, Document, Object)):
        raise TypeError("Expected Core API container type.")

    if not keys:
        return None
    elif len(keys) == 1:
        return remove(node, keys[0])

    key = keys[0]
    next = node[key]
    child = deep_remove(next, keys[1:])
    return replace(node, key, child)


def deep_replace(node, keys, value):
    """
    Return a new immutable container type, with the given nested key replaced.
    """
    if not isinstance(node, (Array, Document, Object)):
        raise TypeError("Expected Core API container type.")

    if not keys:
        return value
    elif len(keys) == 1:
        return replace(node, keys[0], value)

    key = keys[0]
    next = node[key]
    child = deep_replace(next, keys[1:], value)
    return replace(node, key, child)


# The Core API primatives:

class Document(Mapping):
    """
    The Core API document type.

    Expresses the data that the client may access,
    and the actions that the client may perform.
    """

    def __init__(self, url=None, title=None, content=None):
        if title is None and content is None and isinstance(url, dict):
            url, content = None, url

        if url is not None and not isinstance(url, string_types):
            raise TypeError("'url' must be a string.")
        if title is not None and not isinstance(title, string_types):
            raise TypeError("'title' must be a string.")
        if content is not None and not isinstance(content, dict):
            raise TypeError("'content' must be a dict.")
        if content is not None and any([
            not isinstance(key, string_types) for key in content.keys()
        ]):
            raise TypeError('Document keys must be strings.')

        self._url = '' if (url is None) else url
        self._title = '' if (title is None) else title
        self._data = {} if (content is None) else {
            key: _make_immutable(value) for key, value in content.items()
        }

    def __setattr__(self, key, value):
        if key in ('_data', '_url', '_title'):
            return object.__setattr__(self, key, value)
        raise TypeError("'Document' object does not support property assignment")

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        items = sorted(self._data.items(), key=_key_sorting)
        return iter([key for key, value in items])

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return _document_repr(self)

    def __str__(self):
        return _document_str(self)

    @property
    def url(self):
        return self._url

    @property
    def title(self):
        return self._title

    def action(self, keys, **kwargs):
        """
        Perform an action by calling one of the links in the document tree.
        Returns a new document, or `None` if the current document was removed.
        """
        if not isinstance(keys, (list, tuple)):
            raise TypeError("'keys' must be a list of strings.")
        if any([
            not isinstance(key, string_types) and not isinstance(key, int)
            for key in keys
        ]):
            raise TypeError("'keys' must be a list of strings or ints.")

        # Determine the link node being acted on, and its parent document.
        # 'node' is the link we're calling the action for.
        # 'document_keys' is the list of keys to the link's parent document.
        node = self
        document = self
        document_keys = []
        for idx, key in enumerate(keys, start=1):
            node = node[key]
            if isinstance(node, Document):
                document = node
                document_keys = keys[:idx]

        # Ensure that we've correctly indexed into a link.
        if not isinstance(node, Link):
            raise ValueError(
                "Can only call 'action' on a Link. Got type '%s'." % type(node)
            )
        link = node

        # Perform the action, and return a new document.
        ret = link._transition(document, **kwargs)

        # If we got an error response back, raise an exception.
        if isinstance(ret, Error):
            raise ErrorMessage(ret.messages)

        # Return the new document or other media.
        if link.trans in ('follow', 'create'):
            return ret
        elif ret is None:
            return deep_remove(self, document_keys)
        return deep_replace(self, document_keys, ret)


class Object(Mapping):
    """
    An immutable mapping of strings to values.
    """
    def __init__(self, *args, **kwargs):
        data = dict(*args, **kwargs)
        for key, value in data.items():
            if not isinstance(key, string_types):
                raise TypeError('Object keys must be strings.')
            data[key] = _make_immutable(value)
        self._data = data

    def __setattr__(self, key, value):
        if key == '_data':
            return object.__setattr__(self, key, value)
        raise TypeError("'Object' object does not support property assignment")

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        items = sorted(self._data.items(), key=_key_sorting)
        return iter([key for key, value in items])

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return 'Object(%s)' % _document_repr(self)

    def __str__(self):
        return _document_str(self)


class Array(Sequence):
    """
    An immutable list type container.
    """
    def __init__(self, *args):
        self._data = [
            _make_immutable(value)
            for value in list(*args)
        ]
        if any([isinstance(item, Link) for item in self._data]):
            raise TypeError("Array may not contain 'Link' items.")

    def __setattr__(self, key, value):
        if key == '_data':
            return object.__setattr__(self, key, value)
        raise TypeError("'Array' object does not support property assignment")

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __eq__(self, other):
        return (
            (isinstance(other, Array) and (self._data == other._data)) or
            self._data == other
        )

    def __repr__(self):
        return 'Array(%s)' % _document_repr(self)

    def __str__(self):
        return _document_str(self)


class Link(object):
    """
    Links represent the actions that a client may perform.
    """
    def __init__(self, url=None, trans=None, fields=None, func=None):
        if (url is not None) and (not isinstance(url, string_types)):
            raise TypeError("Argument 'url' must be a string.")
        if (trans is not None) and (not isinstance(trans, string_types)):
            raise TypeError("Argument 'trans' must be a string.")
        if (trans is not None) and (trans not in _transition_types):
            raise ValueError('Invalid transition type for link "%s".' % trans)
        if (fields is not None) and (not isinstance(fields, list)):
            raise TypeError("Argument 'fields' must be a list.")
        if (fields is not None) and any([
            not (isinstance(item, string_types) or isinstance(item, Field))
            for item in fields
        ]):
            raise TypeError("Argument 'fields' must be a list of strings or fields.")

        self._url = '' if (url is None) else url
        self._trans = 'follow' if (trans is None) else trans
        self._fields = () if (fields is None) else tuple([
            item if isinstance(item, Field) else Field(item, required=False)
            for item in fields
        ])
        self._func = _default_link_func if func is None else func

    @property
    def url(self):
        return self._url

    @property
    def trans(self):
        return self._trans

    @property
    def fields(self):
        return self._fields

    def _validate(self, **parameters):
        """
        Ensure that parameters passed to the link are correct.

        Raises a `ValueError` if any parameters do not validate.
        """
        provided = set(parameters.keys())
        required = set([
            field.name for field in self.fields if field.required
        ])
        optional = set([
            field.name for field in self.fields if not field.required
        ])

        # Determine any parameter names supplied that are not valid.
        unexpected = provided - (optional | required)
        unexpected = ['"' + item + '"' for item in sorted(unexpected)]
        if unexpected:
            prefix = len(unexpected) > 1 and 'parameters ' or 'parameter '
            raise ValueError('Unknown ' + prefix + ', '.join(unexpected))

        # Determine if any required field names not supplied.
        missing = required - provided
        missing = ['"' + item + '"' for item in sorted(missing)]
        if missing:
            prefix = len(missing) > 1 and 'parameters ' or 'parameter '
            raise ValueError('Missing required ' + prefix + ', '.join(missing))

        # Ensure all parameter values are valid types.
        for value in parameters.values():
            _validate_parameter(value)

    def _fields_as_string(self):
        """
        Return the fields as a string containing all the field names,
        indicating which fields are required and which are optional.

        In this display we order fields with required fields first.

        For example: "text, [completed]"
        """
        return ', '.join([
            field.name for field in self.fields if field.required
        ] + [
            '[%s]' % field.name for field in self.fields if not field.required
        ])

    def _fields_as_repr(self):
        """
        Return the fields as a repr string.

        For example: "required('text'), 'completed'"
        """
        return ', '.join([
            'required(%s)' % repr(field.name)
            if field.required else
            repr(field.name)
            for field in self.fields
        ])

    def _transition(self, document, **parameters):
        """
        Call a link and return a new document or other media.
        """
        self._validate(**parameters)
        return self._func(document=document, link=self, **parameters)

    def __setattr__(self, key, value):
        if key in ('_url', '_trans', '_fields', '_func'):
            return object.__setattr__(self, key, value)
        raise TypeError("'Link' object does not support property assignment")

    def __eq__(self, other):
        return (
            isinstance(other, Link) and
            self.url == other.url and
            self.trans == other.trans and
            set(self.fields) == set(other.fields)
        )

    def __repr__(self):
        args = "url=%s" % repr(self.url)
        if self.trans != _default_transition_type:
            args += ", trans=%s" % repr(self.trans)
        if self.fields:
            args += ", fields=[%s]" % self._fields_as_repr()
        return "Link(%s)" % args

    def __str__(self):
        return _document_str(self)


class Error(object):
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

    def __setattr__(self, key, value):
        if key in ('_messages'):
            return object.__setattr__(self, key, value)
        raise TypeError("'Error' object does not support property assignment")

    def __eq__(self, other):
        return (
            (
                isinstance(other, Error) and
                (self.messages == other.messages)
            ) or self.messages == other
        )

    def __repr__(self):
        return 'Error(%s)' % repr(list(self.messages))

    def __str__(self):
        return '<Error>' + ''.join([
            '\n    * %s' % repr(message) for message in self.messages
        ])

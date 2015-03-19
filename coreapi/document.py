# coding: utf-8
from collections import Mapping, Sequence
from coreapi.compat import is_string
from coreapi.exceptions import DocumentError


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
        is_string(value) or
        value is None or
        isinstance(value, (int, float, bool, Document, Object, Array, Link))
    ):
        return value

    msg = "Invalid type in document. Got '%s'." % type(value)
    raise DocumentError(msg)


def _document_sorting(item):
    """
    Document sorting: 'meta' first, then regular attributes
    sorted alphabetically, then links sorted alphabetically.
    """
    key, value = item
    if isinstance(value, Link):
        return (2, key)
    elif key != 'meta':
        return (1, key)
    return (0, key)


def _object_sorting(item):
    """
    Object sorting: Regular attributes sorted alphabetically,
    then links sorted alphabetically.
    """
    key, value = item
    if isinstance(value, Link):
        return (1, key)
    return (0, key)


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


def _document_str(node, indent=0):
    """
    Return a verbose, indented representation of a Document or other primative.
    """
    if isinstance(node, (Document, Object)):
        head_indent = '    ' * indent
        body_indent = '    ' * (indent + 1)

        body = ',\n'.join([
            body_indent + repr(key) + ': ' + _document_str(value, indent + 1)
            for key, value in node.items()
        ])

        if isinstance(node, Document):
            head = '<%s%s>' % (
                node.title.strip() or 'Document',
                ' ' + repr(node.url) if node.url else ''
            )
            return head + '\n' + body
        return '{\n' + body + '\n' + head_indent + '}'

    elif isinstance(node, Array):
        head_indent = '    ' * indent
        body_indent = '    ' * (indent + 1)

        body = ',\n'.join([
            body_indent + _document_str(value, indent + 1)
            for value in node
        ])

        return '[\n' + body + '\n' + head_indent + ']'

    elif isinstance(node, Link):
        return 'link(%s)' % node._fields_as_string()

    return repr(node)


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
        self._url = '' if (url is None) else url
        self._title = '' if (title is None) else title
        data = {} if (content is None) else dict(content)

        for key, value in data.items():
            if not is_string(key):
                raise DocumentError('Document keys must be strings.')
            data[key] = _make_immutable(value)
        self._data = data

    def __setattr__(self, key, value):
        if key in ('_data', '_url', '_title'):
            return object.__setattr__(self, key, value)
        raise TypeError("'Document' object does not support property assignment")

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        items = sorted(self._data.items(), key=_document_sorting)
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

        # Perform the action, and return a new document.
        ret = node.call(document, **kwargs)
        if ret is None:
            return deep_remove(self, document_keys)
        return deep_replace(self, document_keys, ret)


class Object(Mapping):
    """
    An immutable mapping of strings to values.
    """
    def __init__(self, *args, **kwargs):
        data = dict(*args, **kwargs)
        for key, value in data.items():
            if not is_string(key):
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
        items = sorted(self._data.items(), key=_object_sorting)
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
    def __init__(self, url=None, rel=None, fields=None, action=None):
        self.url = url
        self.rel = rel
        self.fields = [] if (fields is None) else fields
        self.action = action

    def _validate(self, **kwargs):
        """
        Ensure that arguments passed to the link are correct.

        Raises a `ValueError` if any arguments do not validate.
        """
        provided = set(kwargs.keys())

        # Get sets of field names for both required and optional fields.
        required = set([
            field.get('name') for field in self.fields
            if field.get('required', True)
        ])
        optional = set([
            field.get('name') for field in self.fields
            if not field.get('required', True)
        ])

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

    def _fields_as_string(self):
        """
        Return the fields as a string containing all the field names,
        indicating which fields are required and which are optional.

        For example: "text, [completed]"
        """
        def field_as_string(field):
            if field.get('required', True):
                return field.get('name')
            return '[' + field.get('name') + ']'

        return ', '.join([
            field_as_string(field) for field in self.fields
        ])

    def call(self, document, **kwargs):
        from coreapi.transport import HTTPTransport
        self._validate(**kwargs)
        if self.action:
            return self.action(document, **kwargs)
        transport = HTTPTransport()
        return transport.follow(url=self.url, rel=self.rel, arguments=kwargs)

    def __eq__(self, other):
        return (
            isinstance(other, Link) and
            self.url == other.url and
            self.rel == other.rel and
            self.fields == other.fields
        )

    def __repr__(self):
        args = "url=%s" % repr(self.url)
        if self.rel:
            args += ", rel=%s" % (self.rel)
        if self.fields:
            args += ", fields=%s" % repr(self.fields)
        return "Link(%s)" % args

#coding: utf-8
from collections import Mapping
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
    Return the representation of a document or other primative
    in plain python style. Only the outermost element gets the
    class wrapper.
    """
    if isinstance(node, (Document, Object)):
        return '{%s}' % ', '.join([
            '%s: %s' % (repr(key), _document_repr(value))
            for key, value in node.items()
        ])
    elif isinstance(node, Array):
        return '[%s]' % ', '.join([
            _document_repr(value) for value in node
        ])
    return repr(node)


class Document(Mapping):
    def __init__(self, *args, **kwargs):
        data = dict(*args, **kwargs)
        for key, value in data.items():
            if not is_string(key):
                raise DocumentError('Document keys must be strings.')
            data[key] = _make_immutable(value)
        self._data = data

    def __setattr__(self, key, value):
        if key == '_data':
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
        return 'Document(%s)' % _document_repr(self)


class Object(Mapping):
    """
    An immutable mapping of strings to values.
    """
    def __init__(self, *args, **kwargs):
        data = dict(*args, **kwargs)
        for key, value in data.items():
            assert is_string(key), 'Object keys must be strings.'
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


class Array(tuple):
    """
    An immutable list type container.
    """
    def __init__(self, *args):
        data = [
            _make_immutable(value)
            for value in tuple(*args)
        ]
        return super(Array, self).__init__(data)

    def __setattr__(self, key, value):
        raise TypeError("'Array' object does not support property assignment")

    def __repr__(self):
        return 'Array(%s)' % _document_repr(self)


class Link(object):
    def __init__(self, url=None, rel=None, fields=None):
        self.url = url
        self.rel = rel
        self.fields = [] if (fields is None) else fields

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

    def __call__(self, **kwargs):
        assert self._parent is not None, (
            "Cannot call this link as it is not attached to a document."
        )
        self._validate(**kwargs)
        transport = _get_default_transport()
        document = transport.follow(url=self.url, rel=self.rel, arguments=kwargs)
        if self.rel in (None, 'follow'):
            return document

        root_document = self._get_root()
        parent_document = self._get_parent_document()
        if self.rel == 'delete':
            return _copy_with_remove(root_document, parent_document)
        return _copy_with_replace(root_document, parent_document, document)

    def __repr__(self):
        return "<Link url='%s' rel='%s' fields=(%s)>" % (
            self.url, self.rel, self._fields_as_string()
        )


### Formatted printing of DocJSON documents.

def _coreapi_repr(obj, indent=0):
    """
    Returns an indented string representation for a document.
    """
    if isinstance(obj, (Document, Object)):
        final_idx = len(obj) - 1
        ret = '{\n'
        for idx, (key, val) in enumerate(obj.items()):
            ret += '    ' * (indent + 1) + key
            if isinstance(val, Link):
                ret += '(' + val._fields_as_string() + ')'
            else:
                ret += ': ' + _coreapi_repr(val, indent + 1)
            ret += idx == final_idx and '\n' or ',\n'
        ret += '    ' * indent + '}'
        return ret

    elif isinstance(obj, Array):
        final_idx = len(obj) - 1
        ret = '[\n'
        for idx, val in enumerate(obj):
            ret += '    ' * (indent + 1) + _coreapi_repr(val, indent + 1)
            ret += idx == final_idx and '\n' or ',\n'
        ret += '    ' * indent + ']'
        return ret

    if is_string(obj):
        return "'" + str(obj) + "'"

    return repr(obj)

#coding: utf-8
from collections import Mapping, OrderedDict
from coreapi.compat import is_string, urlparse
import re


# <TODO Notes - http://127.0.0.1:3000/>
#     add_note(description)
#     notes: [
#         <Note - http://127.0.0.1:3000/626579bd-b2ba-40d0-92af-9ff0bfa5f276>
#             complete: False
#             description: 'blah!'
#             delete()
#             edit(description, complete)
#         <Note - http://127.0.0.1:3000/626579bd-b2ba-40d0-92af-9ff0bfa5f276>
#             complete: False
#             description: 'blah!'
#             delete()
#             edit(description, complete)
#     ]

# Regex for valid python identifiers
_PYTHON_IDENTIFIER = re.compile(r"^[^\d\W]\w*\Z", re.UNICODE)


def _get_default_transport():
    # One of those odd edge cases where a circular import
    # is actually reasonable.
    from coreapi.transport import HTTPTransport
    return HTTPTransport()


def _copy_with_replace(doc, replace_from, replace_to):
    if doc == replace_from:
        return replace_to

    if isinstance(doc, Document):
        return Document({
            key: _copy_with_replace(value, replace_from, replace_to)
            for key, value in doc.items()
        })
    elif isinstance(doc, Object):
        return Object({
            key: _copy_with_replace(value, replace_from, replace_to)
            for key, value in doc.items()
        })
    elif isinstance(doc, List):
        return List([
            _copy_with_replace(item, replace_from, replace_to)
            for item in doc
        ])
    elif isinstance(doc, Link):
        return Link(doc.url, doc.rel, doc.fields)
    return doc


def _copy_with_remove(doc, remove_from):
    if doc == remove_from:
        return None

    if isinstance(doc, Document):
        return Document({
            key: _copy_with_remove(value, remove_from)
            for key, value in doc.items()
            if value is not remove_from
        })
    elif isinstance(doc, Object):
        return Object({
            key: _copy_with_remove(value, remove_from)
            for key, value in doc.items()
            if value is not remove_from
        })
    elif isinstance(doc, List):
        return List([
            _copy_with_remove(item, remove_from)
            for item in doc
            if item is not remove_from
        ])
    elif isinstance(doc, Link):
        return Link(doc.url, doc.rel, doc.fields)
    return doc


class Document(Mapping):
    def __init__(self, data):
        self._data = OrderedDict(data)
        self._parent = None
        for child in self.values():
            if isinstance(child, (Document, Object, List, Link)):
                child._parent = self

    def _get_root(self):
        if self._parent is None:
            return self
        return self._parent._get_root()

    def __getattr__(self, attr):
        # Support attribute style lookup eg. `document.meta.title`
        try:
            return self._data[attr]
        except KeyError:
            raise AttributeError("document has no attribute '%s'" % attr)

    def __getitem__(self, key):
        # Delegate mapping implementation to the `_data` ordered dict.
        return self._data[key]

    def __iter__(self):
        # Delegate mapping implementation to the `_data` ordered dict.
        return iter(self._data)

    def __len__(self):
        # Delegate mapping implementation to the `_data` ordered dict.
        return len(self._data)

    def __dir__(self):
        # Return class methods plus all valid python identifiers that are keys
        # of the document. Used for tab completion in interactive python shell.
        attr_keys = [key for key in self._data if _PYTHON_IDENTIFIER.match(key)]
        return list(set(dir(Document) + attr_keys))

    def __str__(self):
        return "%s - %s" % (self.meta.get('title', '<no title>'), self.meta.url)

    def __repr__(self):
        return _coreapi_repr(self)


class Link(object):
    def __init__(self, url=None, rel=None, fields=None):
        self.url = url
        self.rel = rel
        self.fields = [] if (fields is None) else fields
        self._parent = None

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

    def _get_root(self):
        if self._parent is None:
            return self
        return self._parent._get_root()

    def _get_parent_document(self):
        node = self._parent
        while not isinstance(node, Document):
            node = node._parent
        return node

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


class List(tuple):
    """
    This class is an immutable list-like object, that prints the
    contained data using a nice indented representation.
    """
    def __init__(self, *args):
        super(List, self).__init__(*args)
        for child in self:
            if isinstance(child, (Document, Object, List, Link)):
                child._parent = self

    def _get_root(self):
        if self._parent is None:
            return self
        return self._parent._get_root()

    def __repr__(self):
        return _coreapi_repr(self)


class Object(Mapping):
    """
    This class is an immutable ordered dictionary, that also allows
    us to access the attributes as properties on the object.

    For example: `doc.author.name` will lookup doc['author']['name'].

    It also prints the contained data using a nice indented representation.
    """
    def __init__(self, *args, **kwargs):
        self._data = OrderedDict(*args, **kwargs)
        self._parent = None
        for child in self.values():
            if isinstance(child, (Document, Object, List, Link)):
                child._parent = self

    def _get_root(self):
        if self._parent is None:
            return self
        return self._parent._get_root()

    def __getattr__(self, attr):
        # Allow 'doc.meta.title' style as a shortcut to "doc['meta']['title']"
        try:
            return self[attr]
        except KeyError:
            raise AttributeError("object has no attribute '%s'" % attr)

    def __getitem__(self, key):
        # Delegate mapping implementation to the `_data` ordered dict.
        return self._data[key]

    def __iter__(self):
        # Delegate mapping implementation to the `_data` ordered dict.
        return iter(self._data)

    def __len__(self):
        # Delegate mapping implementation to the `_data` ordered dict.
        return len(self._data)

    def __dir__(self):
        # Return class methods plus all valid python identifiers that are keys
        # of the document.  Used for tab completion in interactive python shell.
        attr_keys = [key for key in self._data if identifier.match(key)]
        return list(set(dir(Object) + attr_keys))

    def __repr__(self):
        return _coreapi_repr(self)


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

    elif isinstance(obj, List):
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

from __future__ import unicode_literals
from coreapi.codecs.base import BaseCodec
from coreapi.document import Document, Link, Array, Object, Error, Field


def _to_repr(node):
    if isinstance(node, Document):
        content = ', '.join([
            '%s: %s' % (repr(key), _to_repr(value))
            for key, value in node.items()
        ])
        return 'Document(url=%s, title=%s, content={%s})' % (
            repr(node.url), repr(node.title), content
        )

    elif isinstance(node, Error):
        content = ', '.join([
            '%s: %s' % (repr(key), _to_repr(value))
            for key, value in node.items()
        ])
        return 'Error(title=%s, content={%s})' % (
            repr(node.title), content
        )

    elif isinstance(node, Object):
        return '{%s}' % ', '.join([
            '%s: %s' % (repr(key), _to_repr(value))
            for key, value in node.items()
        ])

    elif isinstance(node, Array):
        return '[%s]' % ', '.join([
            _to_repr(value) for value in node
        ])

    elif isinstance(node, Link):
        args = "url=%s" % repr(node.url)
        if node.action:
            args += ", action=%s" % repr(node.action)
        if node.encoding:
            args += ", encoding=%s" % repr(node.encoding)
        if node.transform:
            args += ", transform=%s" % repr(node.transform)
        if node.fields:
            fields_repr = ', '.join(_to_repr(item) for item in node.fields)
            args += ", fields=[%s]" % fields_repr
        return "Link(%s)" % args

    elif isinstance(node, Field):
        args = repr(node.name)
        if not node.required and not node.location:
            return args
        if node.required:
            args += ', required=True'
        if node.location:
            args += ', location=%s' % repr(node.location)
        return 'Field(%s)' % args

    return repr(node)


class PythonCodec(BaseCodec):
    """
    A Python representation of a Document, for use with '__repr__'.
    """
    media_type = 'text/python'
    supports = ['encoding']

    def dump(self, node, **kwargs):
        # Object and Array only have the class name wrapper if they
        # are the outermost element.
        if isinstance(node, Object):
            return 'Object(%s)' % _to_repr(node)
        elif isinstance(node, Array):
            return 'Array(%s)' % _to_repr(node)
        return _to_repr(node)

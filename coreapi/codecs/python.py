from __future__ import unicode_literals
from coreapi.document import Document, Link, Array, Object, Error


def _to_repr(node):
    if isinstance(node, Document):
        content = ', '.join([
            '%s: %s' % (repr(key), _to_repr(value))
            for key, value in node.items()
        ])
        return 'Document(url=%s, title=%s, content={%s})' % (
            repr(node.url), repr(node.title), content
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
        if node.trans != 'follow':
            args += ", trans=%s" % repr(node.trans)
        if node.fields:
            fields_repr = ', '.join([
                'required(%s)' % repr(field.name)
                if field.required else
                repr(field.name)
                for field in node.fields
            ])
            args += ", fields=[%s]" % fields_repr
        return "Link(%s)" % args

    elif isinstance(node, Error):
        return 'Error(%s)' % repr(list(node.messages))

    return repr(node)


class PythonCodec(object):
    """
    A Python representation of a Document, for use with '__repr__'.
    """

    def dump(self, node):
        # Object and Array only have the class name wrapper if they
        # are the outermost element.
        if isinstance(node, Object):
            return 'Object(%s)' % _to_repr(node)
        elif isinstance(node, Array):
            return 'Array(%s)' % _to_repr(node)
        return _to_repr(node)

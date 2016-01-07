from __future__ import unicode_literals
from coreapi.codecs.base import BaseCodec
from coreapi.document import Document, Link, Array, Object, Error
import click
import json


def _colorize_document(text):
    return click.style(text, fg='green')  # pragma: nocover


def _colorize_keys(text):
    return click.style(text, fg='cyan')  # pragma: nocover


def _to_plaintext(node, indent=0, base_url=None, colorize=False):
    colorize_document = _colorize_document if colorize else lambda x: x
    colorize_keys = _colorize_keys if colorize else lambda x: x

    if isinstance(node, Document):
        head_indent = '    ' * indent
        body_indent = '    ' * (indent + 1)

        body = '\n'.join([
            body_indent + colorize_keys(str(key) + ': ') +
            _to_plaintext(value, indent + 1, base_url=base_url, colorize=colorize)
            for key, value in node.data.items()
        ] + [
            body_indent + colorize_keys(str(key) + '(') +
            _fields_to_plaintext(value, colorize=colorize) + colorize_keys(')')
            for key, value in node.links.items()
        ])

        head = colorize_document('<%s %s>' % (
            node.title.strip() or 'Document',
            json.dumps(node.url)
        ))
        return head if (not body) else head + '\n' + body

    elif isinstance(node, Object):
        head_indent = '    ' * indent
        body_indent = '    ' * (indent + 1)

        body = '\n'.join([
            body_indent + colorize_keys(str(key)) + ': ' +
            _to_plaintext(value, indent + 1, base_url=base_url, colorize=colorize)
            for key, value in node.data.items()
        ] + [
            body_indent + colorize_keys(str(key) + '(') +
            _fields_to_plaintext(value, colorize=colorize) + colorize_keys(')')
            for key, value in node.links.items()
        ])

        return '{}' if (not body) else '{\n' + body + '\n' + head_indent + '}'

    elif isinstance(node, Array):
        head_indent = '    ' * indent
        body_indent = '    ' * (indent + 1)

        body = ',\n'.join([
            body_indent + _to_plaintext(value, indent + 1, base_url=base_url, colorize=colorize)
            for value in node
        ])

        return '[]' if (not body) else '[\n' + body + '\n' + head_indent + ']'

    elif isinstance(node, Link):
        return (
            colorize_keys('link(') +
            _fields_to_plaintext(node, colorize=colorize) +
            colorize_keys(')')
        )

    elif isinstance(node, Error):
        return '<Error>' + ''.join([
            '\n    * %s' % repr(message) for message in node.messages
        ])

    return json.dumps(node)


def _fields_to_plaintext(link, colorize=False):
    colorize_keys = _colorize_keys if colorize else lambda x: x

    return colorize_keys(', ').join([
        field.name for field in link.fields if field.required
    ] + [
        '[%s]' % field.name for field in link.fields if not field.required
    ])


class PlainTextCodec(BaseCodec):
    """
    A plaintext representation of a Document, intended for readability.
    """
    media_type = 'text/plain'

    def dump(self, node, colorize=False, **kwargs):
        return _to_plaintext(node, colorize=colorize)

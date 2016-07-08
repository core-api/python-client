from coreapi import codecs, exceptions, transports
from coreapi.compat import string_types
from coreapi.document import Document, Link
from coreapi.utils import determine_transport
import collections
import itypes


LinkAncestor = collections.namedtuple('LinkAncestor', ['document', 'keys'])


def _lookup_link(document, keys):
    """
    Validates that keys looking up a link are correct.

    Returns a two-tuple of (link, link_ancestors).
    """
    if not isinstance(keys, (list, tuple)):
        msg = "'keys' must be a list of strings or ints."
        raise TypeError(msg)
    if any([
        not isinstance(key, string_types) and not isinstance(key, int)
        for key in keys
    ]):
        raise TypeError("'keys' must be a list of strings or ints.")

    # Determine the link node being acted on, and its parent document.
    # 'node' is the link we're calling the action for.
    # 'document_keys' is the list of keys to the link's parent document.
    node = document
    link_ancestors = [LinkAncestor(document=document, keys=[])]
    for idx, key in enumerate(keys):
        try:
            node = node[key]
        except (KeyError, IndexError, TypeError):
            index_string = ''.join('[%s]' % repr(key).strip('u') for key in keys)
            msg = 'Index %s did not reference a link. Key %s was not found.'
            raise exceptions.LinkLookupError(msg % (index_string, repr(key).strip('u')))
        if isinstance(node, Document):
            ancestor = LinkAncestor(document=node, keys=keys[:idx + 1])
            link_ancestors.append(ancestor)

    # Ensure that we've correctly indexed into a link.
    if not isinstance(node, Link):
        index_string = ''.join('[%s]' % repr(key).strip('u') for key in keys)
        msg = "Can only call 'action' on a Link. Index %s returned type '%s'."
        raise exceptions.LinkLookupError(
            msg % (index_string, type(node).__name__)
        )

    return (node, link_ancestors)


class Client(itypes.Object):
    DEFAULT_TRANSPORTS = [
        transports.HTTPTransport()
    ]
    DEFAULT_DECODERS = [
        codecs.CoreJSONCodec(), codecs.JSONCodec(), codecs.TextCodec()
    ]

    def __init__(self, decoders=None, transports=None):
        if decoders is None:
            decoders = self.DEFAULT_DECODERS
        if transports is None:
            transports = self.DEFAULT_TRANSPORTS
        self._decoders = itypes.List(decoders)
        self._transports = itypes.List(transports)

    @property
    def decoders(self):
        return self._decoders

    @property
    def transports(self):
        return self._transports

    def get(self, url, force_codec=False):
        link = Link(url, action='get')

        # Perform the action, and return a new document.
        transport = determine_transport(self.transports, link.url)
        return transport.transition(link, self.decoders, force_codec=force_codec)

    def reload(self, document, force_codec=False):
        url = document.url
        link = Link(url, action='get')

        # Perform the action, and return a new document.
        transport = determine_transport(self.transports, link.url)
        return transport.transition(link, self.decoders, force_codec=force_codec)

    def action(self, document, keys, params=None, action=None, encoding=None, transform=None):
        if isinstance(keys, string_types):
            keys = [keys]

        # Validate the keys and link parameters.
        link, link_ancestors = _lookup_link(document, keys)

        if (action is not None) or (encoding is not None) or (transform is not None):
            # Handle any explicit overrides.
            action = link.action if (action is None) else action
            encoding = link.encoding if (encoding is None) else encoding
            transform = link.transform if (transform is None) else transform
            link = Link(link.url, action=action, encoding=encoding, transform=transform, fields=link.fields)

        # Perform the action, and return a new document.
        transport = determine_transport(self.transports, link.url)
        return transport.transition(link, self.decoders, params=params, link_ancestors=link_ancestors)

from coreapi.codecs import CoreJSONCodec, HALCodec, HTMLCodec, PlainTextCodec
from coreapi.compat import string_types, urlparse
from coreapi.document import Document, Link
from coreapi.exceptions import LinkLookupError, NotAcceptable, UnsupportedContentType, TransportError
from coreapi.transports import HTTPTransport
import collections
import itypes


LinkAncestor = collections.namedtuple('LinkAncestor', ['document', 'keys'])


def lookup_link(document, keys):
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
        except (KeyError, IndexError):
            index_string = ''.join('[%s]' % repr(key).strip('u') for key in keys)
            msg = 'Index %s did not reference a link. Key %s was not found.'
            raise LinkLookupError(msg % (index_string, repr(key).strip('u')))
        if isinstance(node, Document):
            ancestor = LinkAncestor(document=node, keys=keys[:idx + 1])
            link_ancestors.append(ancestor)

    # Ensure that we've correctly indexed into a link.
    if not isinstance(node, Link):
        index_string = ''.join('[%s]' % repr(key).strip('u') for key in keys)
        msg = "Can only call 'action' on a Link. Index %s returned type '%s'."
        raise LinkLookupError(
            msg % (index_string, type(node).__name__)
        )

    return (node, link_ancestors)


class Client(itypes.Object):
    def __init__(self, codecs=None, transports=None):
        if codecs is None:
            codecs = [CoreJSONCodec(), HALCodec(), HTMLCodec(), PlainTextCodec()]
        if transports is None:
            transports = [HTTPTransport()]

        self._codecs = itypes.List(codecs)
        self._transports = itypes.List(transports)
        self._decoders = [
            codec for codec in codecs
            if not getattr(codec.load, 'not_implemented', False)
        ]
        self._encoders = [
            codec for codec in codecs
            if not getattr(codec.dump, 'not_implemented', False)
        ]

    @property
    def codecs(self):
        return self._codecs

    @property
    def encoders(self):
        return self._encoders

    @property
    def decoders(self):
        return self._decoders

    @property
    def transports(self):
        return self._transports

    def get_accept_header(self):
        """
        Return an 'Accept' header for the given codecs.
        """
        return ', '.join([codec.media_type for codec in self.decoders])

    def negotiate_decoder(self, content_type=None):
        """
        Given the value of a 'Content-Type' header, return the appropriate
        codec registered to decode the request content.
        """
        if content_type is None:
            return self.decoders[0]

        content_type = content_type.split(';')[0].strip().lower()
        for codec in self.decoders:
            if codec.media_type == content_type:
                break
        else:
            msg = "Unsupported media in Content-Type header '%s'" % content_type
            raise UnsupportedContentType(msg)

        return codec

    def negotiate_encoder(self, accept=None):
        """
        Given the value of a 'Accept' header, return a two tuple of the appropriate
        content type and codec registered to encode the response content.
        """
        if accept is None:
            return self.encoders[0]

        acceptable = set([
            item.split(';')[0].strip().lower()
            for item in accept.split(',')
        ])

        for codec in self.encoders:
            if codec.media_type in acceptable:
                return codec

        for codec in self.encoders:
            if codec.media_type.split('/')[0] + '/*' in acceptable:
                return codec

        if '*/*' in acceptable:
            return self.encoders[0]

        msg = "Unsupported media in Accept header '%s'" % accept
        raise NotAcceptable(msg)

    def determine_transport(self, url):
        """
        Given a URL determine the appropriate transport instance.
        """
        url_components = urlparse.urlparse(url)
        scheme = url_components.scheme.lower()
        netloc = url_components.netloc

        if not scheme:
            raise TransportError("URL missing scheme '%s'." % url)

        if not netloc:
            raise TransportError("URL missing hostname '%s'." % url)

        for transport in self.transports:
            if scheme in transport.schemes:
                break
        else:
            raise TransportError("Unsupported URL scheme '%s'." % scheme)

        return transport

    def get(self, url):
        transport = self.determine_transport(url)
        link = Link(url, action='get')
        return transport.transition(link, client=self)

    def reload(self, document):
        url = document.url
        transport = self.determine_transport(url)
        link = Link(url, action='get')
        return transport.transition(link, client=self)

    def action(self, document, keys, params=None, action=None, inplace=None):
        if isinstance(keys, string_types):
            keys = [keys]

        if params is None:
            params = {}

        # Validate the keys and link parameters.
        link, link_ancestors = lookup_link(document, keys)

        if action is not None or inplace is not None:
            # Handle any explicit overrides.
            action = link.action if (action is None) else action
            inplace = link.inplace if (inplace is None) else inplace
            link = Link(link.url, action, inplace, link.fields)

        # Perform the action, and return a new document.
        transport = self.determine_transport(link.url)
        return transport.transition(link, params, client=self, link_ancestors=link_ancestors)

    def load(self, bytestring, content_type=None):
        """
        Given a bytestring and an optional content_type, return the
        parsed Document.
        """
        codec = self.negotiate_decoder(content_type)
        return codec.load(bytestring)

    def dump(self, document, accept=None, **kwargs):
        """
        Given a document, and an optional accept header, return a two-tuple of
        the selected media type and encoded bytestring.
        """
        codec = self.negotiate_encoder(accept)
        content = codec.dump(document, **kwargs)
        return (codec.media_type, content)

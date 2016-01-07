from coreapi.compat import string_types, urlparse
from coreapi.document import Error
from coreapi.exceptions import ErrorMessage, NotAcceptable, ParseError, TransportError
from coreapi.validation import validate_keys_to_link, validate_parameters
import itypes


class Session(itypes.Object):
    def __init__(self, codecs, transports):
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
        return ', '.join([codec.media_type for codec in self.codecs])

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
            raise ParseError(msg)

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

    def transition(self, url, action=None, params=None):
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

        return transport.transition(url, action, params)

    def action(self, document, keys, **params):
        if isinstance(keys, string_types):
            keys = [keys]

        # Validate the keys and link parameters.
        link, link_ancestors = validate_keys_to_link(document, keys)
        validate_parameters(link, params)

        # Perform the action, and return a new document.
        new_document = self.transition(link.url, link.action, params)

        # If we got an error response back, raise an exception.
        if isinstance(new_document, Error):
            raise ErrorMessage(new_document.messages)

        # Return the new document or other media.
        transition = link.transition
        if not transition and link.action.lower() in ('put', 'patch', 'delete'):
            transition = 'inline'

        if transition == 'inline':
            keys_to_link_parent = link_ancestors[-1].keys
            if new_document is None:
                return document.delete_in(keys_to_link_parent)
            return document.set_in(keys_to_link_parent, new_document)
        return new_document

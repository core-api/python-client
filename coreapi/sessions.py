from coreapi.compat import urlparse
from coreapi.exceptions import NotAcceptable, ParseError, TransportError
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

    def transition(self, url, action=None, parameters=None):
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

        return transport.transition(url, action, parameters)

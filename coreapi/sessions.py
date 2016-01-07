from collections import OrderedDict
from coreapi.codecs import CoreJSONCodec, HTMLCodec
from coreapi.compat import urlparse
from coreapi.transport import HTTPTransport
from coreapi.exceptions import NotAcceptable, ParseError, TransportError


class DefaultSession(object):
    codecs = OrderedDict([
        ('application/vnd.coreapi+json', CoreJSONCodec),
        ('text/html', HTMLCodec)
    ])
    transports = {
        'http': HTTPTransport,
        'https': HTTPTransport
    }

    def get_accept_header(self):
        return ', '.join(self.codecs.keys())

    def negotiate_decoder(self, content_type=None):
        """
        Given the value of a 'Content-Type' header, return the appropriate
        codec registered to decode the request content.
        """
        if content_type is None:
            return CoreJSONCodec()

        content_type = content_type.split(';')[0].strip().lower()
        try:
            codec_class = self.codecs[content_type]
        except KeyError:
            raise ParseError(
                "Cannot parse unsupported content type '%s'" % content_type
            )

        if not hasattr(codec_class, 'load'):
            raise ParseError(
                "Cannot parse content type '%s'. This implementation only "
                "supports rendering for that content." % content_type
            )

        return codec_class()

    def negotiate_encoder(self, accept=None):
        """
        Given the value of a 'Accept' header, return a two tuple of the appropriate
        content type and codec registered to encode the response content.
        """
        if accept is None:
            key, codec_class = list(self.codecs.items())[0]
            return codec_class()

        media_types = set([
            item.split(';')[0].strip().lower()
            for item in accept.split(',')
        ])

        for key, codec_class in self.codecs.items():
            if key in media_types:
                return codec_class()

        for key, codec_class in self.codecs.items():
            if key.split('/')[0] + '/*' in media_types:
                return codec_class()

        if '*/*' in media_types:
            key, codec_class = list(self.codecs.items())[0]
            return codec_class()

        raise NotAcceptable()

    def transition(self, url, action=None, parameters=None):
        url_components = urlparse.urlparse(url)
        scheme = url_components.scheme.lower()
        netloc = url_components.netloc

        if not scheme:
            raise TransportError('URL missing scheme "%s".' % url)

        if not netloc:
            raise TransportError('URL missing hostname "%s".' % url)

        try:
            transport_class = self.transports[scheme]
        except KeyError:
            raise TransportError('Unknown URL scheme "%s".' % scheme)

        transport = transport_class()
        return transport.transition(url, action, parameters)

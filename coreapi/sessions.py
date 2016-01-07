from coreapi.codecs import CoreJSONCodec, REGISTERED_CODECS
from coreapi.exceptions import ParseError, NotAcceptable


class DefaultSession(object):
    def negotiate_decoder(self, content_type=None):
        """
        Given the value of a 'Content-Type' header, return the appropriate
        codec registered to decode the request content.
        """
        if content_type is None:
            return CoreJSONCodec()

        content_type = content_type.split(';')[0].strip().lower()
        try:
            codec_class = REGISTERED_CODECS[content_type]
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
            key, codec_class = list(REGISTERED_CODECS.items())[0]
            return codec_class()

        media_types = set([
            item.split(';')[0].strip().lower()
            for item in accept.split(',')
        ])

        for key, codec_class in REGISTERED_CODECS.items():
            if key in media_types:
                return codec_class()

        for key, codec_class in REGISTERED_CODECS.items():
            if key.split('/')[0] + '/*' in media_types:
                return codec_class()

        if '*/*' in media_types:
            key, codec_class = list(REGISTERED_CODECS.items())[0]
            return codec_class()

        raise NotAcceptable()

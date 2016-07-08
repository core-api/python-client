from coreapi import exceptions
from coreapi.compat import urlparse


def determine_transport(transports, url):
    """
    Given a URL determine the appropriate transport instance.
    """
    url_components = urlparse.urlparse(url)
    scheme = url_components.scheme.lower()
    netloc = url_components.netloc

    if not scheme:
        raise exceptions.TransportError("URL missing scheme '%s'." % url)

    if not netloc:
        raise exceptions.TransportError("URL missing hostname '%s'." % url)

    for transport in transports:
        if scheme in transport.schemes:
            return transport

    raise exceptions.TransportError("Unsupported URL scheme '%s'." % scheme)


def negotiate_decoder(decoders, content_type=None):
    """
    Given the value of a 'Content-Type' header, return the appropriate
    codec for decoding the request content.
    """
    if content_type is None:
        return decoders[0]

    content_type = content_type.split(';')[0].strip().lower()
    main_type = content_type.split('/')[0] + '/*'
    for codec in decoders:
        if (codec.media_type == content_type) or (codec.media_type == main_type):
            return codec

    msg = "Unsupported media in Content-Type header '%s'" % content_type
    raise exceptions.UnsupportedContentType(msg)


def negotiate_encoder(encoders, accept=None):
    """
    Given the value of a 'Accept' header, return the appropriate codec for
    encoding the response content.
    """
    if accept is None:
        return encoders[0]

    acceptable = set([
        item.split(';')[0].strip().lower()
        for item in accept.split(',')
    ])

    for codec in encoders:
        if codec.media_type in acceptable:
            return codec

    for codec in encoders:
        if codec.media_type.split('/')[0] + '/*' in acceptable:
            return codec

    if '*/*' in acceptable:
        return encoders[0]

    msg = "Unsupported media in Accept header '%s'" % accept
    raise exceptions.NotAcceptable(msg)

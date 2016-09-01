from coreapi import exceptions
from coreapi.compat import is_file, string_types, text_type, urlparse


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
    wildcard_type = '*/*'

    for codec in decoders:
        if codec.media_type in (content_type, main_type, wildcard_type):
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


def validate_path_param(value, name):
    value = _validate_form_primative(value, name, allow_list=False)
    if not value:
        msg = 'Parameter %s: May not be empty.'
        raise exceptions.ValidationError(msg % name)
    return value


def validate_query_param(value, name):
    return _validate_form_primative(value, name)


def validate_body_param(value, encoding, name):
    if encoding == 'application/json':
        return _validate_json_data(value, name)
    elif encoding == 'multipart/form':
        return _validate_form_object(value, name, allow_files=True)
    elif encoding == 'application/x-www-form-urlencoded':
        return _validate_form_object(value, name)
    elif encoding == 'application/octet-stream':
        if not is_file(value):
            msg = 'Parameter %s: Must be an file upload.'
            raise exceptions.ValidationError(msg % name)
    msg = 'Unsupported encoding "%s" for outgoing request.'
    raise exceptions.TransportError(msg % encoding)


def validate_form_param(value, encoding, name):
    if encoding == 'application/json':
        return _validate_json_data(value, name)
    elif encoding == 'multipart/form':
        return _validate_form_primative(value, name, allow_files=True)
    elif encoding == 'application/x-www-form-urlencoded':
        return _validate_form_primative(value, name)
    msg = 'Unsupported encoding "%s" for outgoing request.'
    raise exceptions.TransportError(msg % encoding)


def _validate_form_object(value, name, allow_files=False):
    if not isinstance(value, dict):
        msg = 'Parameter %s: Must be an object.'
        raise exceptions.ValidationError(msg % name)
    return {
        text_type(item_key): _validate_form_primative(item_val, name, allow_files=allow_files)
        for item_key, item_val in value.items()
    }


def _validate_form_primative(value, name, allow_files=False, allow_list=True):
    """
    Parameters in query parameters or form data should be basic types, that
    have a simple string representation. A list of basic types is also valid.
    """
    if isinstance(value, string_types):
        return value
    elif isinstance(value, bool) or (value is None):
        return {True: 'true', False: 'false', None: ''}[value]
    elif isinstance(value, (int, float)):
        return "%s" % value
    elif allow_list and isinstance(value, (list, tuple)):
        # Only the top-level element may be a list.
        return [
            _validate_form_primative(item, name, allow_files=False, allow_list=False)
            for item in value
        ]
    elif allow_files and is_file(value):
        return value

    msg = 'Parameter %s: Must be a primative type.'
    raise exceptions.ValidationError(msg % name)


def _validate_json_data(value, name):
    if (value is None) or isinstance(value, string_types + (bool, int, float)):
        return value
    elif isinstance(value, (list, tuple)):
        return [_validate_json_data(item, name) for item in value]
    elif isinstance(value, dict):
        return {
            text_type(item_key): _validate_json_data(item_val, name)
            for item_key, item_val in value.items()
        }

    msg = 'Parameter %s: Must be a JSON primative.'
    raise exceptions.ValidationError(msg % name)

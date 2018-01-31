from coreapi import exceptions
from coreapi.compat import string_types, text_type, urlparse, _TemporaryFileWrapper
from collections import namedtuple
import os
import pkg_resources
import tempfile


def domain_matches(request, domain):
    """
    Domain string matching against an outgoing request.
    Patterns starting with '*' indicate a wildcard domain.
    """
    if (domain is None) or (domain == '*'):
        return True

    host = urlparse.urlparse(request.url).hostname
    if domain.startswith('*'):
        return host.endswith(domain[1:])
    return host == domain


def get_installed_codecs():
    packages = [
        (package, package.load()) for package in
        pkg_resources.iter_entry_points(group='coreapi.codecs')
    ]
    return {
        package.name: cls() for (package, cls) in packages
    }


# File utilities for upload and download support.

File = namedtuple('File', 'name content content_type')
File.__new__.__defaults__ = (None,)


def is_file(obj):
    if isinstance(obj, File):
        return True

    if hasattr(obj, '__iter__') and not isinstance(obj, (string_types, list, tuple, dict)):
        # A stream object.
        return True

    return False


def guess_filename(obj):
    name = getattr(obj, 'name', None)
    if name and isinstance(name, string_types) and name[0] != '<' and name[-1] != '>':
        return os.path.basename(name)
    return None


if _TemporaryFileWrapper:
    # Ideally we subclass this so that we can present a custom representation.
    class DownloadedFile(_TemporaryFileWrapper):
        basename = None

        def __repr__(self):
            state = "closed" if self.closed else "open"
            mode = "" if self.closed else " '%s'" % self.file.mode
            return "<DownloadedFile '%s', %s%s>" % (self.name, state, mode)

            def __str__(self):
                return self.__repr__()
else:
    # On some platforms (eg GAE) the private _TemporaryFileWrapper may not be
    # available, just use the standard `NamedTemporaryFile` function
    # in this case.
    DownloadedFile = tempfile.NamedTemporaryFile


# Negotiation utilities. USed to determine which codec or transport class
# should be used, given a list of supported instances.

def determine_transport(transports, url):
    """
    Given a URL determine the appropriate transport instance.
    """
    url_components = urlparse.urlparse(url)
    scheme = url_components.scheme.lower()
    netloc = url_components.netloc

    if not scheme:
        raise exceptions.NetworkError("URL missing scheme '%s'." % url)

    if not netloc:
        raise exceptions.NetworkError("URL missing hostname '%s'." % url)

    for transport in transports:
        if scheme in transport.schemes:
            return transport

    raise exceptions.NetworkError("Unsupported URL scheme '%s'." % scheme)


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
        for media_type in codec.get_media_types():
            if media_type in (content_type, main_type, wildcard_type):
                return codec

    msg = "Unsupported media in Content-Type header '%s'" % content_type
    raise exceptions.NoCodecAvailable(msg)


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
        for media_type in codec.get_media_types():
            if media_type in acceptable:
                return codec

    for codec in encoders:
        for media_type in codec.get_media_types():
            if codec.media_type.split('/')[0] + '/*' in acceptable:
                return codec

    if '*/*' in acceptable:
        return encoders[0]

    msg = "Unsupported media in Accept header '%s'" % accept
    raise exceptions.NoCodecAvailable(msg)


# Validation utilities. Used to ensure that we get consistent validation
# exceptions when invalid types are passed as a parameter, rather than
# an exception occuring when the request is made.

def validate_path_param(value):
    value = _validate_form_field(value, allow_list=False)
    if not value:
        msg = 'Parameter %s: May not be empty.'
        raise exceptions.ParameterError(msg)
    return value


def validate_query_param(value):
    return _validate_form_field(value)


def validate_body_param(value, encoding):
    if encoding == 'application/json':
        return _validate_json_data(value)
    elif encoding == 'multipart/form-data':
        return _validate_form_object(value, allow_files=True)
    elif encoding == 'application/x-www-form-urlencoded':
        return _validate_form_object(value)
    elif encoding == 'application/octet-stream':
        if not is_file(value):
            msg = 'Must be an file upload.'
            raise exceptions.ParameterError(msg)
        return value
    msg = 'Unsupported encoding "%s" for outgoing request.'
    raise exceptions.NetworkError(msg % encoding)


def validate_form_param(value, encoding):
    if encoding == 'application/json':
        return _validate_json_data(value)
    elif encoding == 'multipart/form-data':
        return _validate_form_field(value, allow_files=True)
    elif encoding == 'application/x-www-form-urlencoded':
        return _validate_form_field(value)
    msg = 'Unsupported encoding "%s" for outgoing request.'
    raise exceptions.NetworkError(msg % encoding)


def _validate_form_object(value, allow_files=False):
    """
    Ensure that `value` can be encoded as form data or as query parameters.
    """
    if not isinstance(value, dict):
        msg = 'Must be an object.'
        raise exceptions.ParameterError(msg)
    return {
        text_type(item_key): _validate_form_field(item_val, allow_files=allow_files)
        for item_key, item_val in value.items()
    }


def _validate_form_field(value, allow_files=False, allow_list=True):
    """
    Ensure that `value` can be encoded as a single form data or a query parameter.
    Basic types that has a simple string representation are supported.
    A list of basic types is also valid.
    """
    if isinstance(value, string_types):
        return value
    elif isinstance(value, bool) or (value is None):
        return {True: 'true', False: 'false', None: ''}[value]
    elif isinstance(value, (int, float)):
        return "%s" % value
    elif allow_list and isinstance(value, (list, tuple)) and not is_file(value):
        # Only the top-level element may be a list.
        return [
            _validate_form_field(item, allow_files=False, allow_list=False)
            for item in value
        ]
    elif allow_files and is_file(value):
        return value

    msg = 'Must be a primitive type.'
    raise exceptions.ParameterError(msg)


def _validate_json_data(value):
    """
    Ensure that `value` can be encoded into JSON.
    """
    if (value is None) or isinstance(value, (bool, int, float, string_types)):
        return value
    elif isinstance(value, (list, tuple)) and not is_file(value):
        return [_validate_json_data(item) for item in value]
    elif isinstance(value, dict):
        return {
            text_type(item_key): _validate_json_data(item_val)
            for item_key, item_val in value.items()
        }

    msg = 'Must be a JSON primitive.'
    raise exceptions.ParameterError(msg)

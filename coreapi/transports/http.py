# coding: utf-8
from __future__ import unicode_literals
from collections import OrderedDict
from coreapi.codecs import default_decoders, negotiate_decoder
from coreapi.compat import is_file, urlparse
from coreapi.document import Document, Object, Link, Array, Error
from coreapi.exceptions import ErrorMessage
from coreapi.transports.base import BaseTransport
import collections
import requests
import itypes
import mimetypes
import uritemplate


Params = collections.namedtuple('Params', ['path', 'query', 'headers', 'body', 'data', 'files'])
empty_params = Params({}, {}, {}, None, {}, {})


def _get_method(action):
    if not action:
        return 'GET'
    return action.upper()


def _get_params(method, fields, params=None):
    """
    Separate the params into their location types.
    """
    if params is None:
        return empty_params

    field_map = {field.name: field for field in fields}

    path = {}
    query = {}
    headers = {}
    body = None
    data = {}
    files = {}

    for key, value in params.items():
        if key not in field_map or not field_map[key].location:
            # Default is 'query' for 'GET' and 'DELETE', and 'form' for others.
            location = 'query' if method in ('GET', 'DELETE') else 'form'
        else:
            location = field_map[key].location

        if location == 'path':
            path[key] = value
        elif location == 'query':
            query[key] = value
        elif location == 'header':
            headers[key] = value
        elif location == 'body':
            body = value
        elif location == 'form':
            if is_file(value):
                files[key] = value
            else:
                data[key] = value

    return Params(path, query, headers, body, data, files)


def _get_encoding(encoding, params):
    if encoding:
        return encoding

    if params.body is not None:
        if is_file(params.body):
            return 'application/octet-stream'
        return 'application/json'
    elif params.files:
        return 'multipart/form-data'
    elif params.data:
        return 'application/json'

    return ''


def _get_url(url, path_params):
    """
    Given a templated URL and some parameters that have been provided,
    expand the URL.
    """
    if path_params:
        return uritemplate.expand(url, path_params)
    return url


def _get_headers(url, decoders=None, credentials=None):
    """
    Return a dictionary of HTTP headers to use in the outgoing request.
    """
    if decoders is None:
        decoders = default_decoders

    accept = '%s, */*' % decoders[0].media_type

    headers = {
        'accept': accept,
        'user-agent': 'coreapi'
    }

    if credentials:
        # Include any authorization credentials relevant to this domain.
        url_components = urlparse.urlparse(url)
        host = url_components.hostname
        if host in credentials:
            headers['authorization'] = credentials[host]

    return headers


def _get_content_type(file_obj):
    """
    When a raw file upload is made, determine a content-type where possible.
    """
    name = getattr(file_obj, 'name', None)
    if name is not None:
        content_type, encoding = mimetypes.guess_type(name)
    else:
        content_type = None
    return content_type


def _build_http_request(url, method, headers=None, encoding=None, params=empty_params):
    """
    Make an HTTP request and return an HTTP response.
    """
    opts = {
        "headers": headers or {}
    }

    if params.query:
        opts['params'] = params.query

    if (params.body is not None) or params.data or params.files:
        if encoding == 'application/json':
            if params.body is not None:
                opts['json'] = params.body
            else:
                opts['json'] = params.data
        elif encoding == 'multipart/form-data':
            opts['data'] = params.data
            opts['files'] = params.files
        elif encoding == 'application/x-www-form-urlencoded':
            opts['data'] = params.data
        elif encoding == 'application/octet-stream':
            opts['data'] = params.body
            content_type = _get_content_type(params.body)
            if content_type:
                opts['headers']['content-type'] = content_type

    request = requests.Request(method, url, **opts)
    request = request.prepare()
    return request


def _send_http_request(request):
    session = requests.Session()
    response = session.send(request)
    return response


def _coerce_to_error_content(node):
    """
    Errors should not contain nested documents or links.
    If we get a 4xx or 5xx response with a Document, then coerce
    the document content into plain data.
    """
    if isinstance(node, (Document, Object)):
        # Strip Links from Documents, treat Documents as plain dicts.
        return OrderedDict([
            (key, _coerce_to_error_content(value))
            for key, value in node.data.items()
        ])
    elif isinstance(node, Array):
        # Strip Links from Arrays.
        return [
            _coerce_to_error_content(item)
            for item in node
            if not isinstance(item, Link)
        ]
    return node


def _coerce_to_error(obj, default_title):
    """
    Given an arbitrary return result, coerce it into an Error instance.
    """
    if isinstance(obj, Document):
        return Error(
            title=obj.title or default_title,
            content=_coerce_to_error_content(obj)
        )
    elif isinstance(obj, dict):
        return Error(title=default_title, content=obj)
    elif isinstance(obj, list):
        return Error(title=default_title, content={'messages': obj})
    elif obj is None:
        return Error(title=default_title)
    return Error(title=default_title, content={'message': obj})


def _decode_result(response, decoders=None):
    """
    Given an HTTP response, return the decoded Core API document.
    """
    if response.content:
        # Content returned in response. We should decode it.
        content_type = response.headers.get('content-type')
        codec = negotiate_decoder(content_type, decoders=decoders)
        result = codec.load(response.content, base_url=response.url)
    else:
        # No content returned in response.
        result = None

    # Coerce 4xx and 5xx codes into errors.
    is_error = response.status_code >= 400 and response.status_code <= 599
    if is_error and not isinstance(result, Error):
        result = _coerce_to_error(result, default_title=response.reason)

    return result


def _handle_inplace_replacements(document, link, link_ancestors):
    """
    Given a new document, and the link/ancestors it was created,
    determine if we should:

    * Make an inline replacement and then return the modified document tree.
    * Return the new document as-is.
    """
    if not link.transform:
        if link.action.lower() in ('put', 'patch', 'delete'):
            transform = 'inplace'
        else:
            transform = 'new'
    else:
        transform = link.transform

    if transform == 'inplace':
        root = link_ancestors[0].document
        keys_to_link_parent = link_ancestors[-1].keys
        if document is None:
            return root.delete_in(keys_to_link_parent)
        return root.set_in(keys_to_link_parent, document)

    return document


class HTTPTransport(BaseTransport):
    schemes = ['http', 'https']

    def __init__(self, credentials=None, headers=None, request_callback=None, response_callback=None):
        if headers:
            headers = {key.lower(): value for key, value in headers.items()}
        self._credentials = itypes.Dict(credentials or {})
        self._headers = itypes.Dict(headers or {})
        self._request_callback = request_callback
        self._response_callback = response_callback

    @property
    def credentials(self):
        return self._credentials

    @property
    def headers(self):
        return self._headers

    def transition(self, link, params=None, decoders=None, link_ancestors=None):
        method = _get_method(link.action)
        params = _get_params(method, link.fields, params)
        encoding = _get_encoding(link.encoding, params)
        url = _get_url(link.url, params.path)
        headers = _get_headers(url, decoders, self.credentials)
        headers.update(self.headers)

        request = _build_http_request(url, method, headers, encoding, params)
        if self._request_callback:
            self._request_callback(request)

        response = _send_http_request(request)
        if self._response_callback:
            self._response_callback(response)

        result = _decode_result(response, decoders)

        if isinstance(result, Document) and link_ancestors:
            result = _handle_inplace_replacements(result, link, link_ancestors)

        if isinstance(result, Error):
            raise ErrorMessage(result)

        return result

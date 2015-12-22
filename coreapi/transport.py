# coding: utf-8
from __future__ import unicode_literals
from coreapi.compat import urlparse
from coreapi.codecs import negotiate_decoder, ACCEPT_HEADER
from coreapi.exceptions import TransportError
import logging
import requests
import json


_http_method_map = {
    'follow': 'GET',
    'action': 'POST',
    'create': 'POST',
    'update': 'PUT',
    'delete': 'DELETE'
}


logger = logging.getLogger('coreapi.transport')


def transition(url, trans=None, parameters=None):
    url_components = urlparse.urlparse(url)
    scheme = url_components.scheme.lower()
    netloc = url_components.netloc

    if not scheme:
        raise TransportError('URL missing scheme "%s".' % url)

    if not netloc:
        raise TransportError('URL missing hostname "%s".' % url)

    try:
        transport_class = REGISTERED_SCHEMES[scheme]
    except KeyError:
        raise TransportError('Unknown URL scheme "%s".' % scheme)

    transport = transport_class()
    return transport.transition(url, trans, parameters)


class HTTPTransport(object):
    def transition(self, url, trans=None, parameters=None):
        method = _http_method_map[trans]

        if parameters and method == 'GET':
            opts = {
                'params': parameters,
                'headers': {
                    'accept': ACCEPT_HEADER
                }
            }
        elif parameters:
            opts = {
                'data': json.dumps(parameters),
                'headers': {
                    'content-type': 'application/json',
                    'accept': ACCEPT_HEADER
                }
            }
        else:
            opts = {
                'headers': {
                    'accept': ACCEPT_HEADER
                }
            }

        self.log_request(method, url, opts)
        response = requests.request(method, url, **opts)
        if not response.content:
            return None

        content_type = response.headers.get('content-type')
        codec = negotiate_decoder(content_type)
        return codec.load(response.content, base_url=url)

    def log_request(self, method, url, opts):
        params = opts.get('params', {})
        headers = opts.get('headers', {})
        data = opts.get('data', '')
        url = requests.Request(method, url, params=params).prepare().url
        headers_string = '\n'.join([
            '%s: %s' % (key, value)
            for key, value in headers.items()
        ])
        body_string = '\n' + data if data else ''
        message = "HTTP %s %s\n%s\n%s" % (method, url, headers_string, body_string)
        print message


REGISTERED_SCHEMES = {
    'http': HTTPTransport,
    'https': HTTPTransport
}

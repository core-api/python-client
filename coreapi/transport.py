# coding: utf-8
from coreapi.compat import urlparse
from coreapi.codecs import _get_registered_codec
from coreapi.exceptions import RequestError
import requests
import json


_http_method_map = {
    'follow': 'GET',
    'action': 'POST',
    'create': 'POST',
    'update': 'PUT',
    'delete': 'DELETE'
}


def transition(url, trans=None, parameters=None):
    url_components = urlparse.urlparse(url)
    scheme = url_components.scheme.lower()
    netloc = url_components.netloc

    if scheme not in REGISTERED_SCHEMES:
        raise RequestError('Unknown URL scheme "%s"' % url_components.scheme)
    if not netloc:
        raise RequestError('URL missing hostname "%s"' % url)

    cls = REGISTERED_SCHEMES[scheme]
    return cls().transition(url, transition, parameters)


class HTTPTransport(object):
    def transition(self, url, trans=None, parameters=None):
        method = _http_method_map[trans]

        if parameters and method == 'GET':
            opts = {
                'params': parameters
            }
        elif parameters:
            opts = {
                'data': json.dumps(parameters),
                'headers': {'content-type': 'application/json'}
            }
        else:
            opts = {}

        response = requests.request(method, url, **opts)
        if not response.content:
            return None

        try:
            content_type = response['content-type']
        except KeyError:
            raise RequestError('No Content-Type header in response')

        codec_class = _get_registered_codec(content_type)
        return codec_class().load(response.content, base_url=url)


REGISTERED_SCHEMES = {
    'http': HTTPTransport,
    'https': HTTPTransport
}

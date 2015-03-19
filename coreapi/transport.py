# coding: utf-8
from coreapi.compat import urlparse
from coreapi.codecs import JSONCodec
from coreapi.exceptions import RequestError
import requests
import json


class HTTPTransport(object):
    schemes = ['http', 'https']

    def follow(self, url, rel=None, arguments=None):
        url_components = urlparse.urlparse(url)
        if url_components.scheme.lower() not in self.schemes:
            raise RequestError('Unknown URL scheme "%s"' % url_components.scheme)
        if not url_components.netloc:
            raise RequestError('URL missing hostname "%s"' % url)

        method = {
            'follow': 'GET',
            'action': 'POST',
            'edit': 'PUT',
            'delete': 'DELETE',
            None: 'GET'
        }[rel]

        if arguments and method == 'GET':
            opts = {
                'params': arguments
            }
        elif arguments:
            opts = {
                'data': json.dumps(arguments),
                'headers': {'content-type': 'application/json'}
            }
        else:
            opts = {}

        response = requests.request(method, url, **opts)
        if response.status_code == 204:
            return None
        codec = JSONCodec()
        return codec.loads(response.content, base_url=url)

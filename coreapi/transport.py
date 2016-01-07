# coding: utf-8
from __future__ import unicode_literals
import requests
import itypes
import json


class BaseTransport(itypes.Object):
    schemes = None

    def transition(self, url, action=None, parameters=None):
        raise NotImplementedError()  # pragma: nocover


class HTTPTransport(BaseTransport):
    schemes = ['http', 'https']

    def transition(self, url, action=None, parameters=None):
        from coreapi import get_default_session
        session = get_default_session()

        method = 'GET' if (action is None) else action.upper()
        accept = session.get_accept_header()

        if parameters and method == 'GET':
            opts = {
                'params': parameters,
                'headers': {
                    'accept': accept
                }
            }
        elif parameters:
            opts = {
                'data': json.dumps(parameters),
                'headers': {
                    'content-type': 'application/json',
                    'accept': accept
                }
            }
        else:
            opts = {
                'headers': {
                    'accept': accept
                }
            }

        response = requests.request(method, url, **opts)
        if not response.content:
            return None

        content_type = response.headers.get('content-type')
        codec = session.negotiate_decoder(content_type)
        return codec.load(response.content, base_url=url)

# coding: utf-8
from __future__ import unicode_literals
import requests
import json


class HTTPTransport(object):
    def transition(self, url, action=None, parameters=None):
        from coreapi.sessions import DefaultSession
        session = DefaultSession()

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

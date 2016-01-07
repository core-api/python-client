# coding: utf-8
from __future__ import unicode_literals
from coreapi import Error, ErrorMessage
from coreapi.compat import urlparse
import requests
import itypes
import json


class BaseTransport(itypes.Object):
    schemes = None

    def transition(self, link, params=None, session=None, link_ancestors=None):
        raise NotImplementedError()  # pragma: nocover


class HTTPTransport(BaseTransport):
    schemes = ['http', 'https']

    def __init__(self, credentials=None):
        self._credentials = itypes.Dict(credentials or {})

    @property
    def credentials(self):
        return self._credentials

    def transition(self, link, params=None, session=None, link_ancestors=None):
        if session is None:
            from coreapi import get_default_session
            session = get_default_session()

        response = self.make_http_request(session, link.url, link.action, params)
        document = self.load_document(session, response)
        if isinstance(document, Error):
            raise ErrorMessage(document.messages)

        if link_ancestors:
            document = self.handle_inline_replacements(document, link, link_ancestors)

        return document

    def make_http_request(self, session, url, action=None, params=None):
        """
        Make an HTTP request and return an HTTP response.
        """
        method = 'GET' if (action is None) else action.upper()
        accept = session.get_accept_header()

        if params and method == 'GET':
            opts = {
                'params': params,
                'headers': {
                    'accept': accept
                }
            }
        elif params:
            opts = {
                'data': json.dumps(params),
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

        if self.credentials:
            url_components = urlparse.urlparse(url)
            host = url_components.netloc
            if host in self.credentials:
                opts['headers']['authorization'] = self.credentials[host]

        return requests.request(method, url, **opts)

    def load_document(self, session, response):
        """
        Given an HTTP response, return the decoded Core API document.
        """
        if not response.content:
            return None
        content_type = response.headers.get('content-type')
        codec = session.negotiate_decoder(content_type)
        return codec.load(response.content, base_url=response.url)

    def handle_inline_replacements(self, document, link, link_ancestors):
        """
        Given a new document, and the link/ancestors it was created,
        determine if we should:

        * Make an inline replacement and then return the modified document tree.
        * Return the new document as-is.
        """
        transition_type = link.transition
        if not transition_type and link.action.lower() in ('put', 'patch', 'delete'):
            transition_type = 'inline'

        if transition_type == 'inline':
            root = link_ancestors[0].document
            keys_to_link_parent = link_ancestors[-1].keys
            if document is None:
                return root.delete_in(keys_to_link_parent)
            return root.set_in(keys_to_link_parent, document)
        return document

# coding: utf-8
from __future__ import unicode_literals
from coreapi import Document, Error, ErrorMessage
from coreapi.compat import urlparse
import requests
import itypes
import json
import uritemplate


class BaseTransport(itypes.Object):
    schemes = None

    def transition(self, link, params=None, session=None, link_ancestors=None):
        raise NotImplementedError()  # pragma: nocover


class HTTPTransport(BaseTransport):
    schemes = ['http', 'https']

    def __init__(self, credentials=None, headers=None):
        self._credentials = itypes.Dict(credentials or {})
        self._headers = itypes.Dict(headers or {})

    @property
    def credentials(self):
        return self._credentials

    @property
    def headers(self):
        return self._headers

    def transition(self, link, params=None, session=None, link_ancestors=None):
        if session is None:
            from coreapi import get_default_session
            session = get_default_session()

        method = self.get_http_method(link.action)
        url, query_params, form_params = self.get_params(method, link, params)
        response = self.make_http_request(session, url, method, query_params, form_params)
        document = self.load_document(session, response)
        if isinstance(document, Error):
            raise ErrorMessage(document)

        if link_ancestors:
            document = self.handle_inplace_replacements(document, link, link_ancestors)

        if document is None:
            document = Document(url=response.url)
        return document

    def get_http_method(self, action=None):
        if not action:
            return 'GET'
        return action.upper()

    def get_params(self, method, link, params=None):
        if params is None:
            return (link.url, {}, {})

        fields = {field.name: field for field in link.fields}
        path_params = {}
        query_params = {}
        form_params = {}
        for key, value in params.items():
            if key not in fields or not fields[key].location:
                # Default is 'query' for 'GET'/'DELETE', and 'form' others.
                location = 'query' if method in ('GET', 'DELETE') else 'form'
            else:
                location = fields[key].location

            if location == 'path':
                path_params[key] = value
            elif location == 'query':
                query_params[key] = value
            else:
                form_params[key] = value

        url = uritemplate.expand(link.url, path_params)
        return (url, query_params, form_params)

    def make_http_request(self, session, url, method, query_params=None, form_params=None):
        """
        Make an HTTP request and return an HTTP response.
        """
        opts = {
            "headers": {
                "accept": session.get_accept_header()
            }
        }
        if query_params:
            opts['params'] = query_params
        elif form_params:
            opts['data'] = json.dumps(form_params)
            opts['headers']['content-type'] = 'application/json'

        if self.credentials:
            # Include any authorization credentials relevant to this domain.
            url_components = urlparse.urlparse(url)
            host = url_components.netloc
            if host in self.credentials:
                opts['headers']['authorization'] = self.credentials[host]

        if self.headers:
            # Include any custom headers associated with this transport.
            opts['headers'].update(self.headers)

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

    def handle_inplace_replacements(self, document, link, link_ancestors):
        """
        Given a new document, and the link/ancestors it was created,
        determine if we should:

        * Make an inline replacement and then return the modified document tree.
        * Return the new document as-is.
        """
        if link.inplace is None:
            inplace = link.action.lower() in ('put', 'patch', 'delete')
        else:
            inplace = link.inplace

        if inplace:
            root = link_ancestors[0].document
            keys_to_link_parent = link_ancestors[-1].keys
            if document is None:
                return root.delete_in(keys_to_link_parent)
            return root.set_in(keys_to_link_parent, document)

        return document

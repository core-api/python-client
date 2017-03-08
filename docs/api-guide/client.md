# Clients

In order to interact with an API using Core API, a client instance is required.

The client is used to fetch the initial API description, and to then perform
interactions against the API.

An example client session might look something like this:

    from coreapi import Client

    client = Client()
    document = client.get('https://api.example.org/')
    data = client.action(document, ['flights', 'search'], params={
        'from': 'LHR',
        'to': 'PA',
        'date': '2016-10-12'
    })

---

## Instantiating a client

The default client may be obtained by instantiating an object, without
passing any parameters.

    client = Client()

A client instance holds the configuration about which transports are available
for making network requests, and which codecs are available for decoding the
content of network responses.

The signature of the `Client` class is:

    Client(decoders=None, transports=None, auth=None, session=None)

Arguments:

* `decoders` - A list of decoder instances for decoding the content of responses.
* `transports` - A list of transport instances available for making network requests.
* `auth` - A authentication instance. Used when instantiating the default HTTP transport.
* `session` - A `requests` session instance. Used when instantiating the default HTTP transport.

For example the following would instantiate a client, authenticated using HTTP basic auth,  that is capable of decoding either Core JSON schema responses, or decoding plain JSON
data responses:

    from coreapi import codecs
    from coreapi.auth import BasicAuthentication

    decoders = [
        codecs.CoreJSONCodec(),
        codecs.JSONCodec()
    ]
    auth = BasicAuthentication(domain='*', username='example', password='xxx')
    client = Client(decoders=decoders, auth=auth)

When no arguments are passed, the following defaults are used:

    decoders = [
        codecs.CoreJSONCodec(),     # application/vnd.coreapi+json
        codecs.JSONCodec(),         # application/json
        codecs.TextCodec(),         # text/*
        codecs.DownloadCodec()      # */*
    ]

    transports = [
        transports.HTTPTransport(auth=auth, session=session)  # http, https
    ]

The configured decoders and transports are made available as read-only
properties on a client instance:

* `.decoders`
* `.transports`

---

## Making an initial request

**Signature**: `get(url)`

Make a network request to the given URL. If fetching an API schema or hypermedia
resource, then this should typically return a decoded `Document`.

* `url` - The URL that should be retrieved.
* `format` - Optional. Force the given codec to be used when decoding the response.

For example:

    document = client.get('https://api.example.org/')

---

## Interacting with an API

**Signature**: `action(self, document, keys, params=None)`

Effect an interaction against the given document.

* `document` - A `Document` instance.
* `keys` - A list of strings that index a `Link` within the document.
* `params` - A dictionary of parameters to use for the API interaction.

For example, making a request without any parameters:

    data = client.action(document, ['flights', 'list_airports'])

Or making a request, with parameters included:

    data = client.action(document, ['flights', 'search'], params={
        'from': 'LHR',
        'to': 'PA',
        'date': '2016-10-12'
    })

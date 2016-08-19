# Clients

In order to interact with an API using Core API, a client instance is required.

The client is used to fetch the initial API description, and to then perform
interactions against the API.

An example client session might look something like this:

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

This configuration is set by passing either or both of the `decoders` and
`transports` arguments. The signature of the `Client` class is:

    Client(decoders=None, transports=None)

For example the following would instantiate a client that is capable of
decoding either Core JSON schema responses, or decoding plain JSON
data responses:

    decoders = [
        codecs.CoreJSONCodec(),
        codecs.JSONCodec()
    ]
    client = Client(decoders=decoders)

When no arguments are passed, the following defaults are used:

    decoders = [
        codecs.CoreJSONCodec(),     # application/vnd.coreapi+json
        codecs.JSONCodec(),         # application/json
        codecs.TextCodec()          # text/*
    ]

    transports = [
        transports.HTTPTransport()  # http, https
    ]

The configured decoders and transports are made available as read-only
properties on a client instance:

* `.decoders`
* `.transports`

---

## Making an initial request

* get(url)

Make a network request to the given URL, and return a decoded `Document`.

---

## Interacting with an API

* action(self, document, keys, params=None, overrides=None, validate=True)

Effect an interaction against the given document.

* `keys` - A list of strings that index a link within the document.
* `params` - A dictionary of parameters to use for the API interaction.

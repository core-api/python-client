# Transports

Transports are responsible for making the actual network requests, and handling
the responses.

Whenever an action is taken on a link, the scheme of the URL is inspected, and
the responsibility for making a request is passed to an appropriate transport class.

By default only an HTTP transport implementation is included, but this approach means
that other network protocols can also be supported by Core API, while remaining
transparent to the user of the client library.

## Available transports

### HTTPTransport

The `HTTPTransport` class supports the `http` and `https` schemes.

#### Instantiation

**Signature**: `HTTPTransport(auth=None, headers=None, session=None)`

* `auth` - An authentication instance, or None.
* `headers` - A dictionary of items that should be included in the outgoing request headers.
* `session` - A [requests session instance][sessions] to use when sending requests. This can be used to further customize how HTTP requests and responses are handled, for instance by allowing [transport adapters][transport-adapters] to be attached to the underlying session.

#### Making requests

The following describes how the various Link and Field properties are used when
making an HTTP network request.

**Link.action**

The link `action` property is uppercased and then used to determine the HTTP
method for the request.

If left blank then the `GET` method is used.

**Link.encoding**

The link `encoding` property is used to determine how any `location='form'` or
`location='body'` parameters should be encoded in order to form the body of
the request.

Supported encodings are:

* `'application/json'` - Suitable for primitive and composite types.
* `'application/x-www-form-urlencoded'` - Suitable for primitive types.
* `'multipart/form-data'` - Suitable for primitive types and file uploads.
* `'application/octet-stream'` - Suitable for raw file uploads, with a `location='body'` field.

If left blank and a request body is included, then `'application/json'` is used.

**Link.transform**

The link `transform` property is *only relevant when the link is contained in an
embedded document*. This allows hypermedia documents to effect partial updates.

* `'new'` - The response document should be returned as the result.
* `'inplace'` - The embedded document should be updated in-place, and the resulting
              top-level document returned as the result.

If left blank and a link in an embedded document is acted on, then `'inplace'` is used for `'PUT'`, `'PATCH'`, and `'DELETE'` requests. For any other request `'new'` is used.

**Field.location**

The link `location` property determines how the parameter is used to build the outgoing request.

* `'path'` - The parameter is included in the URL, with the link
             'url' value acting as a [URI template][uri-template].
* `'query'` - The parameter is included as a URL query parameter.
* `'body'` - The parameter is encoded and included as the body of the request.
* `'form'` - The parameter is treated as a single key-value item in an
             dictionary of items. It should be encoded together with any other form
             parameters, and included as the body of the request.

If left blank, then `'query'` is used for `'GET'` and `'DELETE'` requests. For any other request `'form'` is used.

## Custom transports

The transport interface is not yet finalized, as it may still be subject to minor
changes in a future release.

## External packages

No third party transport classes are currently available.

[sessions]: http://docs.python-requests.org/en/master/user/advanced/#session-objects
[transport-adapters]: http://docs.python-requests.org/en/master/user/advanced/#transport-adapters
[uri-template]: https://tools.ietf.org/html/rfc6570

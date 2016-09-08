# Documents

A CoreAPI document is a primitive that may be used to represent either schema of hypermedia responses.

By including information about the available interactions that an API exposes,
the document allows users to interact with the API at an interface level, rather
than a network level.

In the schema case a document will include only links. Interactions to the API
endpoints will typically return plain data.

In the hypermedia case a document will include both links and data. interactions
to the API endpoints will typically return a new document.

---

## Usage

### Retrieving a document

Typically a Document will first be obtained by making a request with a
client instance.

    >>> document = client.get('https://api.example.com/users/')

A document can also be loaded from a raw bytestring, by using a codec instance.

    >>> codec = codecs.CoreJSONCodec()
    >>> bytestring = open('document.corejson', 'rb').read()
    >>> document = codec.decode(bytestring)

### Inspecting a document

A document has some associated metadata that may be inspected.

    >>> document.url
    'https://api.example.com/'
    >>> document.title
    'Example API'

A document may contain content, which may include nested dictionaries and list.
The top level element is always a dictionary. The instance may be accessed using
Python's standard dictionary lookup syntax.

Schema type documents will contain `Link` instances as the leaf nodes in the content.

    >>> document['users']['create']
    Link(url='https://api.example.com/users/', action='post', fields=[...])

Hypermedia documents will also contain `Link` instances, but may also contain
data, or nested `Document` instances.

    >>> document['results']['count']
    45
    >>> document['results']['items'][0]
    Document(url='https://api.example.com/users/0/', content={...})
    >>> document['results']['items'][0]['username']
    'tomchristie'

### Interacting with a document

In order to interact with an API, a document is passed as the first argument to
a client instance. A list of strings indexing into a link in the document is passed
as the second argument.

    >>> data = client.action(document, ['users', 'list'])

Some links may accept a set of parameters, each of which may be either required or optional.

    >>> data = client.action(document, ['users', 'list'], params={'is_admin': True})

A document may be reloaded, by fetching the `document.url` property.

    >>> document = client.get(document.url)  # Reload the current document

---

## Document primitives

When using the `coreapi` library as an API client, you won't typically be instantiating
document instances, but rather retrieving them using the client.

However, if you're using the `coreapi` library on the server-side, you can use
the document primitives directly, in order to create schema or hypermedia representations.
The document should then be encoded using an available codec in order to form the schema response.

### Document

The following are available attributes, and may be passed when instantiating a `Document`:

* `url` - A string giving the canonical URL for this document.
* `title` - A string describing this document.
* `content` - A dictionary containing all the data and links made available by this document.

A document instance also supports dictionary-style lookup on it's contents.

    >>> document['results']['count']
    45

The following properties are available on a document instance, and on any
nested dictionaries it contains:

* `links` - A dictionary-like property including only items that are `Link` instances.
* `data` - A dictionary-like property including only items that are not `Link` instances.

### Link

The following are available attributes, and may be passed when instantiating a `Link`:

* `url` - A string giving the URL against which the request should be made.
* `action` - A string giving the type of outgoing request that should be made.
* `encoding` - A string giving the encoding used for outgoing requests.
* `transform` - A string describing how the response should
* `description` - A string describing this link.
* `fields` - A list of field instances.

Note that the behaviour of link attributes is defined at the transport level,
rather than at the document level. See [the `HTTPTransport` documentation for more details][link-behaviour].

### Field

The following are available attributes, and may be passed when instantiating a `Field`:

* `name` - A string describing a short name for the parameter.
* `required` - A boolean indicating if this is a required parameter on the link.
* `location` - A string describing how this parameter should be included in the outgoing request.
* `description` - A string describing this parameter on the link.

Note that the behaviour of the `location` attribute is defined at the transport level,
rather than at the document level. See [the `HTTPTransport` documentation for more details][link-behaviour].

---

## Handling errors

Error responses are similar to Document responses. Both contain a dictionary of
content. However, an error does not represent a network resource, and so does
not have an associated URL, in the same way as a `Document` does.

When an error response is returned by an API, the `ErrorMessage` exception is raised.
The `Error` instance itself is available on the exception as the `.error` attribute.

    params = {
        'location_code': 'berlin-4353',
        'start_date': '2018-01-03',
        'end_date': '2018-01-07',
        'room_type': 'double',
    }
    try:
        data = client.action(document, ['bookings', 'create'], params=params)
    except coreapi.exceptions.ErrorMessage as exc:
        print("Error: %s" % exc.error)
    else:
        print("Success: %s" % data)

### Error

The following are available attributes, and may be passed when instantiating an `Error`:

* `title` - A string describing the error.
* `content` - A dictionary containing all the data or links made available by this error.


[link-behaviour]: transports.md#link-behaviour

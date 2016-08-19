# Codecs

Codecs are responsible for decoding a bytestring into a `Document` instance,
or for encoding a `Document` instance into a bytestring.

A codec is associated with a media type. For example in HTTP responses,
the `Content-Type` header is used to indicate the media type of
the bytestring returned in the body of the response.

When using a Core API client, HTTP responses are decoded with an appropriate
codec, based on the `Content-Type` of the response.

## Using codecs

All the codecs provided by the `coreapi` library are instantiated without
arguments, for example:

    codec = codecs.CoreJSONCodec()

A codec will provide either one or both of the `decode` or `encode` methods.

### Decoding

* decode(content, url=None)

### Encoding

* encode(document, **options)

### Attributes

The following attributes are available on codec instances:

* `media_type` - A string indicating the media type that the codec represents.
* `supports` - A list of strings, indicating the operations that the codec supports.

The `supports` option should be one of the four following options:

* `['decode', 'encode']`  # Supports both decoding and encoding documents.
* `['decode']`            # Supports decoding documents only.
* `['encode']`            # Supports encoding documents only.
* `['data']`              # Indicates that the codec supports decoding,
                          # but that it is expected to return plain data,
                          # rather than a `Document` object.

---

## Available Codecs

### CoreJSONCodec

Supports decoding or encoding the Core JSON format.

**.media_type**: `application/vnd.coreapi+json`

**.supports**: `['decode', 'encode']`

Example of decoding a Core JSON bytestring into a `Document` instance:

    >>> codec = codecs.TextCodec()
    >>> content = b'{"_type": "document", ...'
    >>> document = codec.decode(content)
    >>> print(document)
    <Flight Search API 'http://api.example.com/'>
        'search': link(from, to, date)

Example of encoding a `Document` instance into a Core JSON bytestring:

    >>> content = codec.encode(document, indent=True)
    >>> print(content)
    {
        "_type": "document"
    }

---

### JSONCodec

Supports decoding JSON data.

**.media_type**: `application/json`

**.supports**: `['data']`

Example:

    >>> codec = codecs.TextCodec()
    >>> content = b'{"string": "abc", "boolean": true, "null": null}'
    >>> data = codec.decode(content)
    >>> print(data)
    {"string": "abc", "boolean": True, "null": None}

---

### TextCodec

Supports decoding plain-text responses.

**.media_type**: `text/*`

**.supports**: `['data']`

Example:

    >>> codec = codecs.TextCodec()
    >>> data = codec.decode(b'hello, world!')
    >>> print(data)
    hello, world!

---

### DisplayCodec

Supports encoding a `Document` to a display representation.

**.media_type**: `text/plain`

**.supports**: `['encoding']`

Example:

    >>> codec = codecs.DisplayCodec()
    >>> content = codec.encode(document, indent=True)
    >>> print(content)
    <Flight Search API 'http://api.example.com/'>
        'search': link(from, to, date)

---

### PythonCodec

Supports encoding a `Document` to an its Python representation.

**.media_type**: `text/python`

**.supports**: `['encoding']`

Example:

    >>> codec = codecs.PythonCodec()
    >>> content = codec.encode(document, indent=True)
    >>> print(content)
    Document(
        title='Flight Search API',
        url='http://api.example.com/',
        content={
            'search': Link(
                url='/search/',
                action='get',
                fields=[
                    Field(name='from'),
                    Field(name='to'),
                    Field(name='date')
                ]
            )
        }
    )

---

## Custom Codecs

Custom codec classes may be created by inheriting from `BaseCodec`, setting
the `media_type` and `supports` properties, and implementing one or both
of the `decode` or `encode` methods.

For example:

    class YAMLCodec(codecs.BaseCodec):
        media_type = 'application/yaml'
        supports = ['data']

        def decode(content, url=None):
            return yaml...

### The codec registry

Tools such as the Core API command line client require a method of discovering
which codecs are installed on the system. This is enabled by using a registry
system.

In order to register a custom codec, the PyPI package must contain a correctly
configured `entry_points` option. Typically this needs to be added in a
`setup.py` module, which is run whenever publishing a new package version.

The `entry_points` option must be a dictionary, containing a `coreapi.codecs`
item listing the available codec classes. As an example, the listing for the
codecs which are registered by the `coreapi` package itself is as follows:

    setup(
        name='coreapi',
        license='BSD',
        ...
        entry_points={
            'coreapi.codecs': [
                'corejson=coreapi.codecs:CoreJSONCodec',
                'json=coreapi.codecs:JSONCodec',
                'text=coreapi.codecs:TextCodec',
            ]
        }
    )

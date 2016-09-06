# Codecs

Codecs are responsible for decoding a bytestring into a `Document` instance,
or for encoding a `Document` instance into a bytestring.

A codec is associated with a media type. For example in HTTP responses,
the `Content-Type` header is used to indicate the media type of
the bytestring returned in the body of the response.

When using a Core API client, HTTP responses are decoded with an appropriate
codec, based on the `Content-Type` of the response.

## Using a Codec

All the codecs provided by the `coreapi` library are instantiated without
arguments, for example:

    codec = codecs.CoreJSONCodec()

A codec will provide either one or both of the `decode` or `encode` methods.

### Decoding

* `decode(bytestring, **options)`

**TODO**

### Encoding

* `encode(document, **options)`

**TODO**

### Attributes

The following attributes are available on codec instances:

* `media_type` - A string indicating the media type that the codec represents.
* `supports` - A list of strings, indicating the operations that the codec supports.

The `supports` option should be one of the four following options:

* `['decode', 'encode']` - Supports both decoding and encoding documents.
* `['decode']` - Supports decoding documents only.
* `['encode']` - Supports encoding documents only.
* `['data']` - Indicates that the codec supports decoding,
               but that it is expected to return plain data,
               rather than a `Document` object.

---

## Available Codecs

### CoreJSONCodec

Supports decoding or encoding the Core JSON format.

**.media_type**: `application/vnd.coreapi+json`

**.supports**: `['decode', 'encode']`

Example of decoding a Core JSON bytestring into a `Document` instance:

    >>> from coreapi import codecs
    >>> codec = codecs.CoreJSONCodec()
    >>> content = b'{"_type": "document", ...}'
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

#### Encoding options

**indent**: Set to `True` for an indented representation. The default is to generate a compact representation.

#### Decoding options

**base_url**: The URL from which the document was retrieved. Used to resolve any relative
URLs in the document.

---

### JSONCodec

Supports decoding JSON data.

**.media_type**: `application/json`

**.supports**: `['data']`

Example:

    >>> from coreapi import codecs
    >>> codec = codecs.JSONCodec()
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

    >>> from coreapi import codecs
    >>> codec = codecs.TextCodec()
    >>> data = codec.decode(b'hello, world!')
    >>> print(data)
    hello, world!

---

### DownloadCodec

Supports decoding arbitrary media as a download file. Returns a temporary file
that will be deleted once it goes out of scope.

**.media_type**: `*/*`

**.supports**: `['data']`

Example:

    >>> from coreapi import codecs
    >>> codec = codecs.DownloadCodec()
    >>> data = codec.decode(b'...')
    >>> print(data)
    <DownloadedFile '.../tmpYbxNXT.download', open 'rb'>

#### Instantiation

By default this codec returns a temporary file that will be deleted once it
goes out of scope. If you want to return temporary files that are not
deleted when they go out of scope then you can instantiate the `DownloadCodec`
with a `download_dir` argument.

For example, to download files to the current working directory:

    >>> import os
    >>> codecs.DownloadCodec(download_dir=os.getcwd())

#### Decoding options

**base_url**: The URL from which the document was retrieved. May be used to
generate an output filename if no `Content-Disposition` header exists.

**content_type**: The response Content-Type header. May be used to determine a
suffix for the output filename if no `Content-Disposition` header exists.

**content_disposition**: The response Content-Disposition header. May be [used to
indicate the download filename][content-disposition-filename].

---

### DisplayCodec

Supports encoding a `Document` to a display representation.

**.media_type**: `text/plain`

**.supports**: `['encoding']`

Example:

    >>> from coreapi import codecs
    >>> codec = codecs.DisplayCodec()
    >>> content = codec.encode(document)
    >>> print(content)
    <Flight Search API 'http://api.example.com/'>
        'search': link(from, to, date)

#### Options

**colorize**: Set to `True` to include ANSI color escapes for terminal representations.
See the Python `click` package [for more details][click-ansi].

---

### PythonCodec

Supports encoding a `Document` to an its Python representation.

**.media_type**: `text/python`

**.supports**: `['encoding']`

Example:

    >>> from coreapi import codecs
    >>> codec = codecs.PythonCodec()
    >>> content = codec.encode(document)
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

    from coreapi import codecs
    import yaml

    class YAMLCodec(codecs.BaseCodec):
        media_type = 'application/yaml'
        supports = ['data']

        def decode(content, **options):
            return yaml.safe_load(content)

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
                'download=coreapi.codecs:DownloadCodec',
            ]
        }
    )

---

## External packages

The following third-party packages are available.

### OpenAPI

A codec for [OpenAPI][openapi] schemas, also known as "Swagger". Installable [from PyPI][openapi-pypi] as `openapi-codec`, and [available on GitHub][openapi-github].

### JSON Hyper-Schema

A codec for [JSON Hyper-Schema][jsonhyperschema]. Installable [from PyPI][jsonhyperschema-pypi] as `jsonhyperschema-codec`, and [available on GitHub][jsonhyperschema-github].

### API Blueprint

A codec for [API Blueprint][apiblueprint] schemas. Installable [from PyPI][apiblueprint-pypi] as `apiblueprint-codec`, and [available on GitHub][apiblueprint-github].

### HAL

A codec for the [HAL][hal] hypermedia format. Installable [from PyPI][hal-pypi] as `hal-codec`, and [available on GitHub][hal-github].

[content-disposition-filename]: https://tools.ietf.org/html/draft-ietf-httpbis-content-disp-00#section-3.3
[click-ansi]: http://click.pocoo.org/5/utils/#ansi-colors

[openapi]: https://openapis.org/specification
[openapi-pypi]: https://pypi.python.org/pypi/openapi-codec
[openapi-github]: https://github.com/core-api/python-openapi-codec

[jsonhyperschema]: http://json-schema.org/latest/json-schema-hypermedia.html
[jsonhyperschema-pypi]: https://pypi.python.org/pypi/jsonhyperschema-codec
[jsonhyperschema-github]: https://github.com/core-api/python-jsonhyperschema-codec

[apiblueprint]: https://apiblueprint.org/
[apiblueprint-pypi]: https://pypi.python.org/pypi/apiblueprint-codec
[apiblueprint-github]: https://github.com/core-api/python-apiblueprint-codec

[hal]: http://stateless.co/hal_specification.html
[hal-pypi]: https://pypi.python.org/pypi/hal-codec
[hal-github]: https://github.com/core-api/python-hal-codec

# Codecs

Codecs are responsible for decoding a bytestring into a `Document` instance,
or for encoding a `Document` instance into a bytestring.

A codec is associated with a media type. For example in HTTP responses,
the `Content-Type` header is used to indicate the media type of
the bytestring returned in the body of the response.

When using a Core API client, HTTP responses are decoded with an appropriate
codec, based on the `Content-Type` of the response.

## Using a codec

All the codecs provided by the `coreapi` library are instantiated without
arguments, for example:

    from coreapi import codecs

    codec = codecs.CoreJSONCodec()

A codec will provide either one or both of the `decode()` or `encode()` methods.

#### Decoding

**Signature**: `decode(bytestring, **options)`

Given a bytestring, returns a decoded `Document`, `Error`, or raw data.

An example of decoding a document:

    bytestring = open('document.corejson', 'rb').read()
    document = codec.decode(bytestring)

The available `options` keywords depend on the codec.

#### Encoding

**Signature**: `encode(document, **options)`

Given a `Document` or `Error`, return an encoded representation as a bytestring.

An example of encoding a document:

    bytestring = codec.encode(document)
    output = open('document.corejson', 'wb')
    output.write(bytestring)
    output.close()

The available `options` keywords depend on the codec.

#### Attributes

The following attribute is available on codec instances:

* `media_type` - A string indicating the media type that the codec represents.

---

## Available codecs

### CoreJSONCodec

Supports decoding or encoding the Core JSON format.

**.media_type**: `application/coreapi+json`

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

Example:

    >>> from coreapi import codecs
    >>> codec = codecs.TextCodec()
    >>> data = codec.decode(b'hello, world!')
    >>> print(data)
    hello, world!

---

### DownloadCodec

Supports decoding arbitrary media as a download file. Returns a [temporary file][tempfile]
that will be deleted once it goes out of scope.

**.media_type**: `*/*`

Example:

    >>> codec = codecs.DownloadCodec()
    >>> download = codec.decode(b'abc...xyz')
    >>> print(download)
    <DownloadedFile '.../tmpYbxNXT.download', open 'rb'>
    >>> content = download.read()
    >>> print(content)
    abc...xyz

The download filename will be determined by either the `Content-Disposition`
header, or based on the request URL and the `Content-Type` header. Download
collisions are avoided by using incrementing filenames where required.
The original name used for the download file can be inspected using `.basename`.

    >>> download = codec.decode(b'abc...xyz', content_type='image/png', base_url='http://example.com/download/')
    >>> download.name
    '/var/folders/2k/qjf3np5s28zf2f58963pz2k40000gn/T/download.png'
    >>> download.basename
    'download.png'

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

## Custom codecs

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

### HAL

A codec for the [HAL][hal] hypermedia format. Installable [from PyPI][hal-pypi] as `hal-codec`, and [available on GitHub][hal-github].

[content-disposition-filename]: https://tools.ietf.org/html/draft-ietf-httpbis-content-disp-00#section-3.3
[click-ansi]: http://click.pocoo.org/5/utils/#ansi-colors
[tempfile]: https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryFile

[openapi]: https://openapis.org/specification
[openapi-pypi]: https://pypi.python.org/pypi/openapi-codec
[openapi-github]: https://github.com/core-api/python-openapi-codec

[jsonhyperschema]: http://json-schema.org/latest/json-schema-hypermedia.html
[jsonhyperschema-pypi]: https://pypi.python.org/pypi/jsonhyperschema-codec
[jsonhyperschema-github]: https://github.com/core-api/python-jsonhyperschema-codec

[hal]: http://stateless.co/hal_specification.html
[hal-pypi]: https://pypi.python.org/pypi/hal-codec
[hal-github]: https://github.com/core-api/python-hal-codec

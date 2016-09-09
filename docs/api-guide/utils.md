# Utilities

The `coreapi.utils` module provides a number of helper functions that
may be useful if writing a custom client or transport class.

---

## File utilities

The following classes are used to indicate upload and download file content.

### File

May be used as a parameter with links that require a file input.

**Signature**: `File(name, content, content_type=None)`

* `name` - The filename.
* `content` - A string, bytestring, or stream object.
* `content_type` - An optional string representing the content type of the file.

An open file or other stream may also be used directly as a parameter, instead
of a `File` instance, but the `File` instance makes it easier to specify the
filename and content in code.

Example:

    >>> from coreapi.utils import File
    >>> upload = File('example.csv', 'a,b,c\n1,2,3\n4,5,6\n')
    >>> data = client.action(document, ['store', 'upload_media'], params={'upload': upload})

### DownloadedFile

A temporary file instance, used to represent downloaded media.

Available attributes:

* `name` - The full filename, including the path.
* `basename` - The filename as determined at the point of download.

Example:

    >>> download = client.action(document, ['user', 'get_profile_image'])
    >>> download.basename
    'avatar.png'
    >>> download.read()
    b'...'

By default the file will be deleted when this object goes out of scope. See
[the `DownloadCodec` documentation][download-codec] for more details.

---

## Negotiation utilities

The following functions are used to determine which of a set of transports
or codecs should be used when performing an API interaction.

### determine_transport

**Signature**: `determine_transport(transports, url)`

Given a list of transports and a URL, return the appropriate transport for
making network requests to that URL.

May raise `NetworkError`.

### negotiate_decoder

**Signature**: `negotiate_decoder(codecs, content_type=None)`

Given a list of codecs, and the value of an HTTP response `Content-Type` header,
return the appropriate codec for decoding the response content.

May raise `NoCodecAvailable`.

### negotiate_encoder

**Signature**: `negotiate_encoder(codecs, accept=None)`

Given a list of codecs, and the value of an incoming HTTP request `Accept`
header, return the appropriate codec for encoding the outgoing response content.

Allows server implementations to provide for client-driven content negotiation.

May raise `NoCodecAvailable`.

---

## Validation utilities

Different request encodings have different capabilities. For example, `application/json`
supports a range of data primitives, but does not support file uploads. In contrast,
`multipart/form-data` only supports string primitives and file uploads.

The following helper functions validate that the types passed to an action are suitable
for use with the given encoding, and ensure that a consistent exception type is raised
if an invalid value is passed.

### validate_path_param

**Signature**: `validate_path_param(value)`

Returns the value, coerced into a string primitive. Validates that the value that is suitable for use in URI-encoded path parameters. Empty strings and composite types such as dictionaries are disallowed.

May raise `ParameterError`.

### validate_query_param

**Signature**: `validate_query_param(value)`

Returns the value, coerced into a string primitive. Validates that the value is suitable for use in URL query parameters.

May raise `ParameterError`.

### validate_body_param

**Signature**: `validate_body_param(value, encoding)`

Returns the value, coerced into a primitive that is valid for the given encoding. Validates that the parameter types provided may be used as the body of the outgoing request.

Valid encodings are `application/json`, `x-www-form-urlencoded`, `multipart/form-data` and `application/octet-stream`.

May raise `ParameterError` for an invalid value, or `NetworkError` for an unsupported encoding.

### validate_form_param

**Signature**: `validate_body_param(value, encoding)`

Returns the value, coerced into a primitive that is valid for the given encoding. Validates that the parameter types provided may be used as a key-value item for part of the body of the outgoing request.

Valid encodings are `application/json`, `x-www-form-urlencoded`, `multipart/form-data`.

May raise `ParameterError`, or `NetworkError` for an unsupported encoding.


[download-codec]: codecs.md#downloadcodec

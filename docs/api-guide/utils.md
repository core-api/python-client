# Utilities

The `coreapi.utils` module provides a number of helper functions that
may be useful if writing a custom client or transport class.

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
`multipart/form` only supports string primatives and file uploads.

The following helper functions validate that the types passed to an action are suitable
for use with the given encoding, and ensure that a consistent exception type is raised
if an invalid value is passed.

### validate_path_param

**Signature**: `validate_path_param(value)`

Returns the value, coerced into a string primitive. Validates that the value that is suitable for use in URI-encoded path parameters. Empty strings and composite types such as dictionaries are disallowed.

May raise `ValidationError`.

### validate_query_param

**Signature**: `validate_query_param(value)`

Returns the value, coerced into a string primitive. Validates that the value is suitable for use in URL query parameters.

May raise `ValidationError`.

### validate_body_param

**Signature**: `validate_body_param(value, encoding)`

Returns the value, coerced into a primitive that is valid for the given encoding. Validates that the parameter types provided may be used as the body of the outgoing request.

Valid encodings are `application/json`, `x-www-form-urlencoded`, `multipart/form` and `application/octet-stream`.

May raise `ValidationError` for an invalid value, or `NetworkError` for an unsupported encoding.

### validate_form_param

**Signature**: `validate_body_param(value, encoding)`

Returns the value, coerced into a primitive that is valid for the given encoding. Validates that the parameter types provided may be used as a key-value item for part of the body of the outgoing request.

Valid encodings are `application/json`, `x-www-form-urlencoded`, `multipart/form`.

May raise `ValidationError`, or `NetworkError` for an unsupported encoding.

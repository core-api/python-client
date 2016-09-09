# Exceptions

Any of the exceptions raised by the `coreapi` library may be imported from the `coreapi.exceptions` module:

    from coreapi.exceptions import CoreAPIException

## The base class

#### CoreAPIException

A base class for all `coreapi` exceptions.

---

## Server errors

The following exception occurs when the server returns an error response.

#### ErrorMessage

The server returned a CoreAPI [Error][error] document.

---

## Client errors

The following exceptions indicate that an incorrect interaction was attempted using the client.

#### LinkLookupError

The keys passed in a [`client.action()`][action] call did not reference a link in the document.

#### ParameterError

The parameters passed in a [`client.action()`][action] call did not match the set of required and optional fields made available by the link, or if the type of parameters passed could
not be supported by the given encoding on the link.

---

## Request errors

The following exceptions indicate that an error occurred when handling
some aspect of the API request.

#### ParseError

A response was returned with malformed content.

#### NoCodecAvailable

Raised when there is no available codec that can handle the given media.

#### NetworkError

An issue occurred with the network request.


[action]: /api-guide/client.md#interacting-with-an-api
[error]: /api-guide/document.md#error

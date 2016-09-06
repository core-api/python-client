# Exceptions

Any of the exceptions raised by the `coreapi` library may be imported from the `coreapi.exceptions` module:

    from coreapi.exceptions import CoreAPIException

## CoreAPIException

A base class for all `coreapi` exceptions.

## ParseError

A response was returned with malformed content.

## NoCodecAvailable

Raised when there is no available codec that can handle the given media.

## NetworkError

An issue occurred with the network request.

## LinkLookupError

The keys passed in a [`client.action()`][action] call did not reference a link in the document.

## ValidationError

The parameters passed in a [`client.action()`][action] call did not match the set of required and optional fields made available by the link, or if the type of parameters passed could
not be supported by the given encoding on the link.

## ErrorMessage

The server returned a CoreAPI [Error][error].

[action]: /api-guide/client.md#interacting-with-an-api
[error]: /api-guide/document.md#error

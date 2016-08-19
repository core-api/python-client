# Utils

## lookup_elements(document, keys, strict_types=True)

Given a document and a list of keys [...]

## determine_transport(transports, url)

Given a list of transports and a URL, return the appropriate transport for
making network requests to that URL.

May raise `TransportError`


## negotiate_decoder(decoders, content_type=None)

Given a list of codecs, and the value of an HTTP response 'Content-Type' header,
return the appropriate codec for decoding the response content.


May raise `UnsupportedContentType`


## negotiate_encoder(encoders, accept=None)

Given a list of codecs, and the value of an incoming HTTP request 'Accept'
header, return the appropriate codec for encoding the outgoing response content.

May raise `NotAcceptable`

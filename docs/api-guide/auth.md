# Authentication

Authentication instances are responsible for handling the network authentication.

## Using authentication

Typically, you'll provide authentication configuration by passing an authentication instance to the client.

    import coreapi 

    auth = coreapi.auth.BasicAuthentication(username='...', password='...')
    coreapi.Client(auth=auth)

It's recommended that you limit authentication scheme to only provide credentials to endpoints that match the expected domain.

    auth = coreapi.auth.BasicAuthentication(
        username='...',
        password='...',
        domain='api.example.com'
    )

You can also provide wildcard domains:

    auth = coreapi.auth.BasicAuthentication(
        username='...',
        password='...',
        domain='*.example.com'
    )

---

## Available authentication schemes

The following authentication schemes are provided as built-in options...

### BasicAuthentication

Uses [HTTP Basic Authentication][basic-auth].

**Signature**: `BasicAuthentication(username, password, domain='*')`

### TokenAuthentication

Uses [HTTP Bearer token authentication][bearer-auth], and can be used for OAuth 2, JWT, and custom token authentication schemes.

Outgoing requests will include the provided token in the request`Authorization` headers, in the following format:

    Authorization: Bearer xxxx-xxxxxxxx-xxxx

The prefix may be customized if required, in order to support HTTP authentication schemes that are not [officially registered][http-auth-schemes].

A typical authentication flow using `TokenAuthentication` would be:

* Using an unauthenticated client make a request providing the users credentials to an endpoint to that returns an API token.
* Instantiate an authenticated client using the returned token, and use this for all future requests.

**Signature**: `TokenAuthentication(token, prefix='Bearer', domain='*')`

### SessionAuthentication

This authentication scheme enables cookies in order to allow a session cookie to be saved and maintained throughout the client's session.

In order to support CSRF protected sessions, this scheme also supports saving CSRF tokens in the incoming response cookies, and mirroring those tokens back to the server by using a CSRF header in any subsequent outgoing requests.

A typical authentication flow using `SessionAuthentication` would be:

* Using an unauthenticated client make an initial request to an endpoint that returns a CSRF cookie.
* Use the unauthenticated client to make a request to a login endpoint, providing the users credentials.
* Subsequent requests by the client will now be authenticated.

**Signature**: `SessionAuthentication(csrf_cookie_name=None, csrf_header_name=None, domain='*')`

---

## Custom authentication

Custom authentication classes may be created by subclassing `requests.AuthBase`, and implmenting the following:

* Set the `allow_cookies` class attribute to either `True` or `False`.
* Provide a `__call__(self, request)` method, which should return an authenticated request instance.

[basic-auth]: https://tools.ietf.org/html/rfc7617
[bearer-auth]: https://tools.ietf.org/html/rfc6750
[http-auth-schemes]: https://www.iana.org/assignments/http-authschemes/
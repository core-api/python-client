# [Python client library][docs]

[![build-status-image]][travis]
[![pypi-version]][pypi]

Python client library for [Core API][core-api].

**Requirements**: Python 2.7, 3.3+

---

## Installation

Install from PyPI, using pip:

    $ pip install coreapi

## Quickstart

Create a client instance:

    from coreapi import Client
    client = Client()

Retrieve an API schema:

    document = client.get('https://api.example.org/')

Interact with the API:

    data = client.action(document, ['flights', 'search'], params={
        'from': 'LHR',
        'to': 'PA',
        'date': '2016-10-12'
    })

## Supported formats

The following schema and hypermedia formats are currently supported, either
through built-in support, or as a third-party codec:

Name                | Media type                 | Notes
--------------------|----------------------------|------------------------------------
CoreJSON            | `application/coreapi+json` | Supports both Schemas & Hypermedia.
OpenAPI ("Swagger") | `application/openapi+json` | Schema support.
JSON Hyper-Schema   | `application/schema+json`  | Schema support.
HAL                 | `application/hal+json`     | Hypermedia support.

Additionally, the following plain data content types are supported:

Name        | Media type         | Notes
------------|--------------------|---------------------------------
JSON        | `application/json` | Returns Python primitive types.
Plain text  | `text/*`           | Returns a Python string instance.
Other media | `*/*`              | Returns a temporary download file.

---

## License

Copyright © 2015-2016, Tom Christie.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.
Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

[docs]: http://core-api.github.io/python-client/
[core-api]: https://github.com/core-api/core-api/
[build-status-image]: https://secure.travis-ci.org/core-api/python-client.svg?branch=master
[travis]: http://travis-ci.org/core-api/python-client?branch=master
[pypi-version]: https://img.shields.io/pypi/v/coreapi.svg
[pypi]: https://pypi.python.org/pypi/coreapi

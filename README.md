# Python client library

Python client library for [Core API][core-api].

[![build-status-image]][travis]
[![pypi-version]][pypi]

**Requirements**: Python 2.7, 3.3, 3.4.

**Test coverage**: 100%

---

### Installation

To install, use pip.

    pip install coreapi

---

### Retrieving and inspecting documents

To initially access a Core API interface, use the `get()` method.

    >>> import coreapi
    >>> doc = coreapi.get('http://coreapi.herokuapp.com')

We can now inspect the returned document.

    >>> print(doc)
    <Notes 'http://coreapi.herokuapp.com/'>
        'notes': [
            <Note '/e7785f34-2b74-41d2-ab3f-f754f688987c/'>
                'complete': False,
                'description': 'Schedule design meeting',
                'delete': link(),
                'edit': link([description], [complete]),
            <Note '/626579bd-b2ba-40d0-92af-9ff0bfa5f276/'>
                'complete: True,
                'description': 'Write release notes',
                'delete': link(),
                'edit': link([description], [complete])
        ],
        'add_note': link(description)

Documents are key-value pairs, and their elements can be accessed by indexing into them.

    >>> doc['notes'][0]['description']
    'Schedule design meeting'

You can also inspect the document URL and title.

    >>> doc.url
    'http://coreapi.herokuapp.com/'
    >>> doc.title
    'Notes'

---

### Interacting with documents

Documents in the Python Core API library are immutable objects. To perform a transition we call the `.action()` method and assign the resulting new document.

    >>> doc = doc.action(['add_note'], description='My new note.')

The first argument to `.action()` is a list of strings or integers, indexing the link to act on. Any extra keyword arguments are passed as parameters to the link.

Transitions may update of the document tree.

    >>> doc = doc.action(['notes', 0, 'edit'], complete=True)
    >>> doc['notes'][0]['complete']
    True

Or they may remove part of the document tree.

    >>> while doc['notes']:
    >>>     doc = doc.action(['notes', 0, 'delete'])
    >>> len(doc['notes'])
    0

---

### Saving and loading documents

To save or load documents into raw bytestrings, use `dump()` and `load()`.

For example, to save a document to disk.

    content_type, content = coreapi.dump(doc)
    file = open('doc.json', 'wb')
    file.write(content)
    file.close()

To load the same document back again.

    file = open('doc.json', 'rb')
    content = file.read()
    file.close()
    doc = coreapi.load(content)

---

## License

Copyright © 2015, Tom Christie.
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

[core-api]: https://github.com/core-api/core-api/
[build-status-image]: https://secure.travis-ci.org/core-api/python-client.svg?branch=master
[travis]: http://travis-ci.org/core-api/python-client?branch=master
[pypi-version]: https://img.shields.io/pypi/v/coreapi.svg
[pypi]: https://pypi.python.org/pypi/coreapi

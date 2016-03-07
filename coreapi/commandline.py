from coreapi.compat import force_bytes, string_types, text_type, urlparse
import click
import coreapi
import json
import os
import sys


config_path = None

document_path = None
history_path = None
credentials_path = None
headers_path = None
bookmarks_path = None


def setup_paths():
    global config_path, document_path, history_path
    global credentials_path, headers_path, bookmarks_path

    default_dir = os.path.join(os.path.expanduser('~'), '.coreapi')
    config_path = os.environ.get('COREAPI_CONFIG_DIR', default_dir)

    document_path = os.path.join(config_path, 'document.json')
    history_path = os.path.join(config_path, 'history.json')
    credentials_path = os.path.join(config_path, 'credentials.json')
    headers_path = os.path.join(config_path, 'headers.json')
    bookmarks_path = os.path.join(config_path, 'bookmarks.json')


def coerce_key_types(doc, keys):
    """
    Given a document and a list of keys such as ['rows', '123', 'edit'],
    return a list of keys, such as ['rows', 123, 'edit'].
    """
    ret = []
    active = doc
    for idx, key in enumerate(keys):
        # Coerce array lookups to integers.
        if isinstance(active, coreapi.Array):
            try:
                key = int(key)
            except:
                pass

        # Descend through the document, so we can correctly identify
        # any nested array lookups.
        ret.append(key)
        try:
            active = active[key]
        except (KeyError, IndexError, ValueError, TypeError):
            ret += keys[idx + 1:]
            break

    return ret


def get_document_string(doc):
    if not doc.title:
        return '<Document %s>' % json.dumps(doc.url)
    return '<%s %s>' % (doc.title, json.dumps(doc.url))


def debug_request(request):
    def request_echo(fmt, *args):
        click.echo(click.style('> ', fg='blue') + (fmt % args))

    headers = request.headers
    headers['host'] = urlparse.urlparse(request.url).hostname

    request_echo(click.style('%s %s HTTP/1.1', bold=True), request.method, request.path_url)
    for key, value in sorted(headers.items()):
        request_echo('%s: %s', key.title(), value)
    if request.body:
        request_echo('')
        for line in request.body.splitlines():
            request_echo(line)


def debug_response(response):
    def success_echo(fmt, *args):
        click.echo(click.style('< ', fg='green') + (fmt % args))

    def failure_echo(fmt, *args):
        click.echo(click.style('< ', fg='red') + (fmt % args))

    def info_echo(fmt, *args):
        click.echo(click.style('< ', fg='yellow') + (fmt % args))

    response_class = ('%s' % response.status_code)[0] + 'xx'
    if response_class == '2xx':
        response_echo = success_echo
    elif response_class in ('4xx', '5xx'):
        response_echo = failure_echo
    else:
        response_echo = info_echo

    response_echo(click.style('%d %s', bold=True), response.status_code, response.reason)
    for key, value in sorted(response.headers.items()):
        response_echo('%s: %s', key.title(), value)
    if response.content:
        response_echo('')
        for line in response.content.splitlines():
            response_echo(line)

    click.echo()


def get_client(decoders=None, debug=False):
    credentials = get_credentials()
    headers = get_headers()
    if debug:
        callbacks = {
            'request_callback': debug_request,
            'response_callback': debug_response
        }
    else:
        callbacks = {}
    http_transport = coreapi.transports.HTTPTransport(credentials, headers, **callbacks)
    return coreapi.Client(decoders=decoders, transports=[http_transport])


def get_document():
    if not os.path.exists(document_path):
        return None
    store = open(document_path, 'rb')
    content = store.read()
    store.close()
    codec = coreapi.codecs.CoreJSONCodec()
    return codec.load(content)


def set_document(doc):
    codec = coreapi.codecs.CoreJSONCodec()
    content = codec.dump(doc)
    store = open(document_path, 'wb')
    store.write(content)
    store.close()


def display(doc):
    if isinstance(doc, (coreapi.Document, coreapi.Error, coreapi.Object, coreapi.Array, coreapi.Link)):
        codec = coreapi.codecs.CoreTextCodec()
        return codec.dump(doc, colorize=True)
    if doc is None:
        return ''
    if isinstance(doc, string_types):
        return doc
    return json.dumps(doc, indent=4, ensure_ascii=False, separators=coreapi.compat.VERBOSE_SEPARATORS)


def json_load_bytes(bytes):
    return json.loads(bytes.decode('utf-8') or '{}')


# Core commands

@click.group(invoke_without_command=True, help='Command line client for interacting with CoreAPI services.\n\nVisit http://www.coreapi.org for more information.')
@click.option('--version', is_flag=True, help='Display the package version number.')
@click.pass_context
def client(ctx, version):
    setup_paths()

    if os.path.isfile(config_path):
        os.remove(config_path)  # pragma: nocover
    if not os.path.isdir(config_path):
        os.mkdir(config_path)

    if ctx.invoked_subcommand is not None:
        return

    if version:
        click.echo('coreapi version %s' % coreapi.__version__)
    else:
        click.echo(ctx.get_help())


@click.command(help='Fetch a document from the given URL.')
@click.argument('url')
@click.option('--debug', '-d', is_flag=True, help='Display the request/response')
@click.option('--format', default=None, type=click.Choice(['corejson', 'hal', 'hyperschema', 'openapi']))
def get(url, debug, format):
    if format:
        decoder = {
            'corejson': coreapi.codecs.CoreJSONCodec(),
            'hal': coreapi.codecs.HALCodec(),
            'hyperschema': coreapi.codecs.HyperschemaCodec(),
            'openapi': coreapi.codecs.OpenAPICodec()
        }[format]
        decoders = [decoder]
    else:
        decoders = None
    client = get_client(decoders=decoders, debug=debug)
    history = get_history()
    try:
        doc = client.get(url)
    except coreapi.exceptions.ErrorMessage as exc:
        click.echo(display(exc.error))
        sys.exit(1)
    click.echo(display(doc))
    if isinstance(doc, coreapi.Document):
        history = history.add(doc)
        set_document(doc)
        set_history(history)


@click.command(help='Load a document from disk.')
@click.argument('input_file', type=click.File('rb'))
@click.option('--format', default='corejson', type=click.Choice(['corejson', 'hal', 'hyperschema', 'openapi']))
def load(input_file, format):
    input_bytes = input_file.read()
    input_file.close()
    decoder = {
        'corejson': coreapi.codecs.CoreJSONCodec(),
        'hal': coreapi.codecs.HALCodec(),
        'hyperschema': coreapi.codecs.HyperschemaCodec(),
        'openapi': coreapi.codecs.OpenAPICodec()
    }[format]

    history = get_history()
    doc = decoder.load(input_bytes)
    click.echo(display(doc))
    if isinstance(doc, coreapi.Document):
        history = history.add(doc)
        set_document(doc)
        set_history(history)


@click.command(help='Clear the active document and other state.\n\nThis includes the current document, history, credentials, headers and bookmarks.')
def clear():
    for path in [
        document_path,
        history_path,
        credentials_path,
        headers_path,
        bookmarks_path
    ]:
        if os.path.exists(path):
            os.remove(path)

    click.echo('Cleared.')


@click.command(help='Display the current document.\n\nOptionally display just the element at the given PATH.')
@click.argument('path', nargs=-1)
def show(path):
    doc = get_document()
    if doc is None:
        click.echo('No current document. Use `coreapi get` to fetch a document first.')
        sys.exit(1)

    if path:
        keys = coerce_key_types(doc, path)
        for key in keys:
            try:
                doc = doc[key]
            except (KeyError, IndexError):
                click.echo('Key %s not found.' % repr(key).strip('u'))
                sys.exit(1)
    click.echo(display(doc))


@click.command(help='Display description for link at given PATH.')
@click.argument('path', nargs=-1)
def describe(path):
    doc = get_document()
    if doc is None:
        click.echo('No current document. Use `coreapi get` to fetch a document first.')
        sys.exit(1)

    if not path:
        click.echo('Missing PATH to a link in the document.')
        sys.exit(1)

    node = doc
    keys = coerce_key_types(doc, path)
    for key in keys:
        try:
            node = node[key]
        except (KeyError, IndexError):
            click.echo('Key %s not found.' % repr(key).strip('u'))
            sys.exit(1)

    if not isinstance(node, coreapi.Link):
        click.echo('Given PATH must index a link, not a %s.' % doc.__class__.__name__)
        sys.exit(1)

    fields_description = any([field.description for field in node.fields])
    if not (node.description or fields_description):
        click.echo('Link has no description.')
        sys.exit(1)

    if node.description:
        click.echo(node.description)
        click.echo()
    for field in node.fields:
        name = field.name if field.required else '[%s]' % field.name
        if field.description:
            click.echo('* %s - %s' % (name, field.description))
        else:
            click.echo('* %s' % name)


def parse_params(ctx, param, value):
    ret = []

    for field, data in value:
        try:
            pair = (field, json.loads(data))
        except:
            pair = (field, data)
        ret.append(pair)

    return ret


def parse_json(ctx, param, value):
    ret = []

    for field, data in value:
        try:
            pair = (field, json.loads(data))
        except:
            raise click.BadParameter('Invalid JSON for data argument "%s"' % field)
        ret.append(pair)

    return ret


@click.command(help='Interact with the active document.\n\nRequires a PATH to a link in the document.\n\nExample:\n\ncoreapi action users add_user --param username tom --param is_admin true')
@click.argument('path', nargs=-1)
@click.option('params', '--param', '-p', type=(text_type, text_type), multiple=True, callback=parse_params, metavar="FIELD VALUE", help='Parameter for the action.')
@click.option('strings', '--string', '-s', type=(text_type, text_type), multiple=True, metavar="FIELD STRING", help='String parameter for the action.')
@click.option('data', '--data', '-d', type=(text_type, text_type), multiple=True, callback=parse_json, metavar="FIELD DATA", help='Data parameter for the action.')
@click.option('files', '--file', '-f', type=(text_type, click.File('rb')), multiple=True, metavar="FIELD FILENAME", help='File parameter for the action.')
@click.option('--action', '-a', metavar="ACTION", help='Set the link action explicitly.', default=None)
@click.option('--encoding', '-e', metavar="ENCODING", help='Set the link encoding explicitly.', default=None)
@click.option('--transform', '-t', metavar="TRANSFORM", help='Set the link transform explicitly.', default=None)
@click.option('--debug', '-d', is_flag=True, help='Display the request/response')
def action(path, params, strings, data, files, action, encoding, transform, debug):
    params = dict(params)
    params.update(dict(strings))
    params.update(dict(data))
    params.update(dict(files))

    if not path:
        click.echo('Missing PATH to a link in the document.')
        sys.exit(1)

    doc = get_document()
    if doc is None:
        click.echo('No current document. Use `coreapi get` to fetch a document first.')
        sys.exit(1)

    client = get_client(debug=debug)
    history = get_history()
    keys = coerce_key_types(doc, path)
    try:
        doc = client.action(
            doc, keys, params=params,
            action=action, encoding=encoding, transform=transform
        )
    except coreapi.exceptions.ErrorMessage as exc:
        click.echo(display(exc.error))
        sys.exit(1)
    except coreapi.exceptions.LinkLookupError as exc:
        click.echo(exc)
        sys.exit(1)
    click.echo(display(doc))
    if isinstance(doc, coreapi.Document):
        history = history.add(doc)
        set_document(doc)
        set_history(history)


@click.command(help='Reload the current document.')
@click.option('--debug', '-d', is_flag=True, help='Display the request/response')
def reload_document(debug):
    doc = get_document()
    if doc is None:
        click.echo('No current document. Use `coreapi get` to fetch a document first.')
        sys.exit(1)

    client = get_client(debug=debug)
    history = get_history()
    try:
        doc = client.reload(doc)
    except coreapi.exceptions.ErrorMessage as exc:
        click.echo(display(exc.error))
        sys.exit(1)
    click.echo(display(doc))
    if isinstance(doc, coreapi.Document):
        history = history.add(doc)
        set_document(doc)
        set_history(history)


# Credentials

def get_credentials():
    if not os.path.isfile(credentials_path):
        return {}
    store = open(credentials_path, 'rb')
    credentials = json_load_bytes(store.read())
    store.close()
    return credentials


def set_credentials(credentials):
    store = open(credentials_path, 'wb')
    store.write(force_bytes(json.dumps(credentials)))
    store.close


@click.group(help='Configure request credentials. Request credentials are associated with a given domain, and used in request "Authorization:" headers.')
def credentials():
    pass


@click.command(help="List stored credentials.")
def credentials_show():
    credentials = get_credentials()
    if credentials:
        width = max([len(key) for key in credentials.keys()])
        fmt = '{domain:%d} "{header}"' % width

    click.echo(click.style('Credentials', bold=True))
    for key, value in sorted(credentials.items()):
        click.echo(fmt.format(domain=key, header=value))


@click.command(help="Add CREDENTIALS string for the given DOMAIN.")
@click.argument('domain', nargs=1)
@click.argument('header', nargs=1)
def credentials_add(domain, header):
    credentials = get_credentials()
    credentials[domain] = header
    set_credentials(credentials)

    click.echo(click.style('Added credentials', bold=True))
    click.echo('%s "%s"' % (domain, header))


@click.command(help="Remove credentials for the given DOMAIN.")
@click.argument('domain', nargs=1)
def credentials_remove(domain):
    credentials = get_credentials()
    credentials.pop(domain, None)
    set_credentials(credentials)

    click.echo(click.style('Removed credentials', bold=True))
    click.echo(domain)


# Headers

def get_headers():
    if not os.path.isfile(headers_path):
        return {}
    headers_file = open(headers_path, 'rb')
    headers = json_load_bytes(headers_file.read())
    headers_file.close()
    return headers


def set_headers(headers):
    headers_file = open(headers_path, 'wb')
    headers_file.write(force_bytes(json.dumps(headers)))
    headers_file.close()


def titlecase(header):
    return '-'.join([word.title() for word in header.split('-')])


@click.group(help="Configure custom request headers.")
def headers():
    pass


@click.command(help="List custom request headers.")
def headers_show():
    headers = get_headers()

    click.echo(click.style('Headers', bold=True))
    for key, value in sorted(headers.items()):
        click.echo(key + ': ' + value)


@click.command(help="Add custom request HEADER with given VALUE.")
@click.argument('header', nargs=1)
@click.argument('value', nargs=1)
def headers_add(header, value):
    header = titlecase(header)
    headers = get_headers()
    headers[header] = value
    set_headers(headers)

    click.echo(click.style('Added header', bold=True))
    click.echo('%s: %s' % (header, value))


@click.command(help="Remove custom request HEADER.")
@click.argument('header', nargs=1)
def headers_remove(header):
    header = titlecase(header)
    headers = get_headers()
    headers.pop(header, None)
    set_headers(headers)

    click.echo(click.style('Removed header', bold=True))
    click.echo(header)


# Headers

def get_bookmarks():
    if not os.path.isfile(bookmarks_path):
        return {}
    bookmarks_file = open(bookmarks_path, 'rb')
    bookmarks = json_load_bytes(bookmarks_file.read())
    bookmarks_file.close()
    return bookmarks


def set_bookmarks(bookmarks):
    bookmarks_file = open(bookmarks_path, 'wb')
    bookmarks_file.write(force_bytes(json.dumps(bookmarks)))
    bookmarks_file.close()


@click.group(help="Add, remove and show bookmarks.")
def bookmarks():
    pass


@click.command(help="List bookmarks.")
def bookmarks_show():
    bookmarks = get_bookmarks()

    if bookmarks:
        width = max([len(key) for key in bookmarks.keys()])
        fmt = '{name:%d} <{title} {url}>' % width

    click.echo(click.style('Bookmarks', bold=True))
    for key, value in sorted(bookmarks.items()):
        click.echo(fmt.format(name=key, title=value['title'] or 'Document', url=json.dumps(value['url'])))


@click.command(help="Add the current document to the bookmarks, with the given NAME.")
@click.argument('name', nargs=1)
def bookmarks_add(name):
    doc = get_document()
    if doc is None:
        click.echo('No current document. Use `coreapi get` to fetch a document first.')
        sys.exit(1)

    bookmarks = get_bookmarks()
    bookmarks[name] = {'url': doc.url, 'title': doc.title}
    set_bookmarks(bookmarks)

    click.echo(click.style('Added bookmark', bold=True))
    click.echo(name)


@click.command(help="Remove a bookmark with the given NAME.")
@click.argument('name', nargs=1)
def bookmarks_remove(name):
    bookmarks = get_bookmarks()
    bookmarks.pop(name, None)
    set_bookmarks(bookmarks)

    click.echo(click.style('Removed bookmark', bold=True))
    click.echo(name)


@click.command(help="Fetch the bookmarked document with the given NAME.")
@click.argument('name', nargs=1)
def bookmarks_get(name):
    bookmarks = get_bookmarks()
    bookmark = bookmarks.get(name)
    if bookmark is None:
        click.echo('Bookmark "%s" does not exist.' % name)
        return
    url = bookmark['url']

    client = get_client()
    history = get_history()
    try:
        doc = client.get(url)
    except coreapi.exceptions.ErrorMessage as exc:
        click.echo(display(exc.error))
        sys.exit(1)
    click.echo(display(doc))
    if isinstance(doc, coreapi.Document):
        history = history.add(doc)
        set_document(doc)
        set_history(history)


# History

def get_history():
    if not os.path.isfile(history_path):
        return coreapi.history.History(max_items=20)
    history_file = open(history_path, 'rb')
    bytestring = history_file.read()
    history_file.close()
    return coreapi.history.load_history(bytestring)


def set_history(history):
    bytestring = coreapi.history.dump_history(history)
    history_file = open(history_path, 'wb')
    history_file.write(bytestring)
    history_file.close()


@click.group(help="Navigate the browser history.")
def history():
    pass


@click.command(help="List the browser history.")
def history_show():
    history = get_history()

    click.echo(click.style('History', bold=True))
    for is_active, doc in history.get_items():
        prefix = '[*] ' if is_active else '[ ] '
        click.echo(prefix + get_document_string(doc))


@click.command(help="Navigate back through the browser history.")
def history_back():
    client = get_client()
    history = get_history()
    if history.is_at_oldest:
        click.echo("Currently at oldest point in history. Cannot navigate back.")
        return
    doc, history = history.back()
    try:
        doc = client.reload(doc)
    except coreapi.exceptions.ErrorMessage as exc:
        click.echo(display(exc.error))
        sys.exit(1)
    click.echo(display(doc))
    if isinstance(doc, coreapi.Document):
        set_document(doc)
        set_history(history)


@click.command(help="Navigate forward through the browser history.")
def history_forward():
    client = get_client()
    history = get_history()
    if history.is_at_most_recent:
        click.echo("Currently at most recent point in history. Cannot navigate forward.")
        return
    doc, history = history.forward()
    try:
        doc = client.reload(doc)
    except coreapi.exceptions.ErrorMessage as exc:
        click.echo(display(exc.error))
        sys.exit(1)
    click.echo(display(doc))
    if isinstance(doc, coreapi.Document):
        set_document(doc)
        set_history(history)


client.add_command(get)
client.add_command(show)
client.add_command(action)
client.add_command(reload_document, name='reload')
client.add_command(clear)
client.add_command(load)
client.add_command(describe)

client.add_command(credentials)
credentials.add_command(credentials_add, name='add')
credentials.add_command(credentials_remove, name='remove')
credentials.add_command(credentials_show, name='show')

client.add_command(headers)
headers.add_command(headers_add, name='add')
headers.add_command(headers_remove, name='remove')
headers.add_command(headers_show, name='show')

client.add_command(bookmarks)
bookmarks.add_command(bookmarks_add, name='add')
bookmarks.add_command(bookmarks_get, name='get')
bookmarks.add_command(bookmarks_remove, name='remove')
bookmarks.add_command(bookmarks_show, name='show')

client.add_command(history)
history.add_command(history_back, name='back')
history.add_command(history_forward, name='forward')
history.add_command(history_show, name='show')


if __name__ == '__main__':
    client()

import click
import coreapi
import os
import sys


class NoDocument(Exception):
    pass


def get_store_path():
    return os.path.join(os.path.expanduser('~'), '.coreapi')


def write_to_store(doc):
    path = get_store_path()
    content_type, content = coreapi.dump(doc)
    store = open(path, 'wb')
    store.write(content)
    store.close()


def read_from_store():
    path = get_store_path()
    if not os.path.exists(path):
        raise NoDocument()
    store = open(path, 'rb')
    content = store.read()
    store.close()
    return coreapi.load(content)


@click.group(invoke_without_command=True, help='Command line client for interacting with CoreAPI services.\n\nVisit http://www.coreapi.org for more information.')
@click.option('--version', is_flag=True, help='Display the package version number.')
@click.pass_context
def client(ctx, version):
    if ctx.invoked_subcommand is not None:
        return

    if version:
        click.echo('coreapi version %s' % coreapi.__version__)
    else:
        click.echo(ctx.get_help())


@click.command(help='Fetch a document from the given URL.')
@click.argument('url')
def get(url):
    doc = coreapi.get(url)
    click.echo(doc)
    write_to_store(doc)


@click.command(help='Remove the current document.')
def clear():
    path = get_store_path()
    if os.path.exists(path):
        os.remove(path)
    click.echo('Document cleared.')


@click.command(help='Display the current document, or element at the given PATH.')
@click.argument('path', nargs=-1)
def show(path):
    try:
        doc = read_from_store()
    except NoDocument:
        click.echo('No current document. Use `coreapi get` to fetch a document first.')
        return

    if path:
        if len(path) > 1:
            click.echo('Too many arguments.')
            sys.exit(1)
        keys = coreapi.dotted_path_to_list(doc, path[0])
        for key in keys:
            doc = doc[key]
        if isinstance(doc, (bool, type(None))):
            doc = {True: 'true', False: 'false', None: 'null'}[doc]
    click.echo(doc)


@click.command(help='Interact with the current document, given a PATH to a link.')
@click.argument('path')
@click.argument('fields', nargs=-1)
def action(path, fields):
    kwargs = {}
    for field in fields:
        if '=' not in field:
            click.echo('All fields should be in format "key=value".')
            sys.exit(1)
        key, value = field.split('=', 1)
        kwargs[key] = value

    try:
        doc = read_from_store()
    except NoDocument:
        click.echo('No current document. Use `coreapi get` to fetch a document first.')
        return

    doc = doc.action(path, **kwargs)
    click.echo(doc)
    write_to_store(doc)


client.add_command(get)
client.add_command(show)
client.add_command(action)
client.add_command(clear)


if __name__ == '__main__':
    client()

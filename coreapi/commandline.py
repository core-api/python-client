import click
import coreapi
import os
import sys


def write_to_store(doc):
    path = os.path.join(os.path.expanduser('~'), '.coreapi')
    content_type, content = coreapi.dump(doc)
    store = open(path, 'wb')
    store.write(content)
    store.close()


def read_from_store():
    path = os.path.join(os.path.expanduser('~'), '.coreapi')
    store = open(path, 'rb')
    content = store.read()
    store.close()
    return coreapi.load(content)


@click.group()
def client():
    pass


@click.command()
@click.argument('url')
def get(url):
    doc = coreapi.get(url)
    click.echo(doc)
    write_to_store(doc)


@click.command()
def show():
    doc = read_from_store()
    click.echo(doc)


@click.command()
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

    doc = read_from_store()
    doc = doc.action(path, **kwargs)
    click.echo(doc)
    write_to_store(doc)


client.add_command(get)
client.add_command(show)
client.add_command(action)


if __name__ == '__main__':
    client()

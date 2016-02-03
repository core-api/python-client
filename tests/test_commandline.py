from click.testing import CliRunner
from coreapi import __version__ as version
from coreapi import Document, Link
from coreapi.commandline import client, coerce_key_types
from coreapi.transports import HTTPTransport
import pytest
import os
import shutil
import tempfile


mock_response = None


def set_response(doc):
    global mock_response
    mock_response = doc


@pytest.fixture(scope="function")
def cli(request):
    """
    A fixture returning a runner for the command line client.
    """
    config_dir = tempfile.mkdtemp()
    os.environ['COREAPI_CONFIG_DIR'] = config_dir
    saved = HTTPTransport.transition

    def transition(*args, **kwargs):
        return mock_response

    def finalize():
        shutil.rmtree(config_dir)
        HTTPTransport.transition = saved

    def _cli(*args):
        return runner.invoke(client, args)

    runner = CliRunner()
    request.addfinalizer(finalize)
    HTTPTransport.transition = transition

    return _cli


# Integration tests

def test_no_command(cli):
    result = cli()
    assert result.output.startswith('Usage:')


def test_version_option(cli):
    result = cli('--version')
    assert result.output == 'coreapi version %s\n' % version


def test_cli_get(cli):
    set_response(Document('http://example.com', 'Example'))
    result = cli('get', 'http://mock')
    assert result.output == '<Example "http://example.com">\n'

    result = cli('show')
    assert result.output == '<Example "http://example.com">\n'


def test_cli_clear(cli):
    set_response(Document('http://example.com', 'Example'))
    result = cli('get', 'http://mock')

    cli('clear')
    result = cli('show')
    assert result.output == 'No current document. Use `coreapi get` to fetch a document first.\n'
    assert result.exit_code == 1


def test_cli_reload(cli):
    result = cli('reload')
    assert result.output == 'No current document. Use `coreapi get` to fetch a document first.\n'
    assert result.exit_code == 1

    set_response(Document('http://example.com', 'Example'))
    result = cli('get', 'http://mock')

    set_response(Document('http://example.com', 'New'))
    cli('reload')
    result = cli('show')
    assert result.output == '<New "http://example.com">\n'


# History

def test_cli_history(cli):
    set_response(Document('http://1.com'))
    result = cli('get', 'http://mock')

    set_response(Document('http://2.com'))
    result = cli('get', 'http://mock')

    result = cli('history', 'show')
    assert result.output == (
        'History\n'
        '[*] <Document "http://2.com">\n'
        '[ ] <Document "http://1.com">\n'
    )

    set_response(Document('http://1.com'))
    result = cli('history', 'back')
    result = cli('history', 'show')
    assert result.output == (
        'History\n'
        '[ ] <Document "http://2.com">\n'
        '[*] <Document "http://1.com">\n'
    )
    result = cli('show')
    assert result.output == '<Document "http://1.com">\n'

    set_response(Document('http://2.com'))
    result = cli('history', 'forward')
    result = cli('history', 'show')
    assert result.output == (
        'History\n'
        '[*] <Document "http://2.com">\n'
        '[ ] <Document "http://1.com">\n'
    )
    result = cli('show')
    assert result.output == '<Document "http://2.com">\n'


# Credentials

def test_cli_credentials(cli):
    result = cli('credentials', 'show')
    assert result.output == 'Credentials\n'

    result = cli('credentials', 'add', 'http://1.com', 'Token 123cat')
    assert result.output == 'Added credentials\nhttp://1.com "Token 123cat"\n'

    result = cli('credentials', 'show')
    assert result.output == 'Credentials\nhttp://1.com "Token 123cat"\n'


# Bookmarks

def test_cli_bookmarks(cli):
    set_response(Document('http://example.com', 'Example'))
    cli('get', 'http://example.com')

    result = cli('bookmarks', 'add', 'example')
    assert result.output == 'Added bookmark\nexample\n'

    result = cli('bookmarks', 'show')
    assert result.output == 'Bookmarks\nexample <Example "http://example.com">\n'

    result = cli('bookmarks', 'get', 'example')
    assert result.output == '<Example "http://example.com">\n'

    result = cli('bookmarks', 'remove', 'example')
    assert result.output == 'Removed bookmark\nexample\n'

    result = cli('bookmarks', 'show')
    assert result.output == 'Bookmarks\n'


# Headers

def test_cli_headers(cli):
    result = cli('headers', 'add', 'Cache-Control', 'public')
    assert result.output == 'Added header\nCache-Control: public\n'

    result = cli('headers', 'show')
    assert result.output == 'Headers\nCache-Control: public\n'

    result = cli('headers', 'remove', 'Cache-Control')
    assert result.output == 'Removed header\nCache-Control\n'

    result = cli('headers', 'show')
    assert result.output == 'Headers\n'


# Test dotted path notation maps to list of keys correctly.

def test_dotted_path_notation():
    doc = Document(content={'rows': [Document(content={'edit': Link()})]})
    keys = coerce_key_types(doc, ['rows', 0, 'edit'])
    assert keys == ['rows', 0, 'edit']


def test_dotted_path_notation_with_invalid_array_lookup():
    doc = Document(content={'rows': [Document(content={'edit': Link()})]})
    keys = coerce_key_types(doc, ['rows', 'zero', 'edit'])
    assert keys == ['rows', 'zero', 'edit']


def test_dotted_path_notation_with_invalid_key():
    doc = Document(content={'rows': [Document(content={'edit': Link()})]})
    keys = coerce_key_types(doc, ['dummy', '0', 'edit'])
    assert keys == ['dummy', '0', 'edit']

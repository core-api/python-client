from coreapi import Document, Link
from coreapi.commandline import client, coerce_key_types
from click.testing import CliRunner
import coreapi
import pytest
import os
import shutil
import tempfile


@pytest.fixture(scope="function")
def runner(request):
    """
    A fixture returning a runner for the command line client.
    """
    config_dir = tempfile.mkdtemp()
    os.environ['COREAPI_CONFIG_DIR'] = config_dir

    def finalize():
        shutil.rmtree(config_dir)

    runner = CliRunner()
    request.addfinalizer(finalize)
    return runner


# Test dotted path notation maps to list of keys correctly.

def test_dotted_path_notation():
    doc = Document({'rows': [Document({'edit': Link()})]})
    keys = coerce_key_types(doc, ['rows', 0, 'edit'])
    assert keys == ['rows', 0, 'edit']


def test_dotted_path_notation_with_invalid_array_lookup():
    doc = Document({'rows': [Document({'edit': Link()})]})
    keys = coerce_key_types(doc, ['rows', 'zero', 'edit'])
    assert keys == ['rows', 'zero', 'edit']


def test_dotted_path_notation_with_invalid_key():
    doc = Document({'rows': [Document({'edit': Link()})]})
    keys = coerce_key_types(doc, ['dummy', '0', 'edit'])
    assert keys == ['dummy', '0', 'edit']


# Integration tests

def test_usage(runner):
    result = runner.invoke(client, ['--version'])
    assert result.output == 'coreapi version %s\n' % coreapi.__version__
    assert result.exit_code == 0

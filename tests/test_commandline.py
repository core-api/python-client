from coreapi import Document, Link
from coreapi.commandline import coerce_key_types


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

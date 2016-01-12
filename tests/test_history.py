from coreapi import Document
from coreapi.history import History, dump_history, load_history
import pytest


def test_empty_history():
    history = History()
    assert history.is_at_most_recent
    assert history.is_at_oldest
    assert history.current is None
    assert list(history.get_items()) == []
    assert load_history(dump_history(history)) == history

    with pytest.raises(ValueError):
        history.back()
    with pytest.raises(ValueError):
        history.forward()

    # Adding blank does not change history.
    new_history = history.add(None)
    assert list(new_history.get_items()) == []

    # Adding new document changes history.
    new_doc = Document('http://example.com', 'Example')
    new_history = history.add(new_doc)
    assert list(new_history.get_items()) == [(True, new_doc)]


def test_single_history():
    doc = Document('http://example.com', 'Example')
    history = History([doc])
    assert history.is_at_most_recent
    assert history.is_at_oldest
    assert history.current == doc
    assert list(history.get_items()) == [(True, doc)]
    assert load_history(dump_history(history)) == history

    with pytest.raises(ValueError):
        history.back()
    with pytest.raises(ValueError):
        history.forward()

    # Adding blank changes history.
    new_history = history.add(None)
    assert list(new_history.get_items()) == [(True, None), (False, doc)]

    # Adding same document does not change history.
    new_doc = Document('http://example.com', 'Example')
    new_history = history.add(new_doc)
    assert list(new_history.get_items()) == [(True, doc)]

    # Adding same URL, different title changes existing item.
    new_doc = Document('http://example.com', 'New')
    new_history = history.add(new_doc)
    assert list(new_history.get_items()) == [(True, new_doc)]

    # Adding different document changes history.
    new_doc = Document('http://other.com', 'Example')
    new_history = history.add(new_doc)
    assert list(new_history.get_items()) == [(True, new_doc), (False, doc)]


def test_navigating_back():
    first = Document('http://first.com', 'First')
    second = Document('http://second.com', 'Second')
    history = History([second, first])
    assert history.is_at_most_recent
    assert not history.is_at_oldest
    assert history.current == second
    assert list(history.get_items()) == [(True, second), (False, first)]

    doc, history = history.back()
    assert doc == first
    assert list(history.get_items()) == [(False, second), (True, first)]


def test_navigating_forward():
    first = Document('http://first.com', 'First')
    second = Document('http://second.com', 'Second')
    history = History([second, first], idx=1)
    assert not history.is_at_most_recent
    assert history.is_at_oldest
    assert history.current == first
    assert list(history.get_items()) == [(False, second), (True, first)]

    doc, history = history.forward()
    assert doc == second
    assert list(history.get_items()) == [(True, second), (False, first)]


def test_adding_from_midpoint():
    """
    Adding an item from midpoint in history removes any forwards items.
    """
    first = Document('http://first.com', 'First')
    second = Document('http://second.com', 'Second')
    history = History([second, first], idx=1)

    third = Document('http://third.com', 'Third')
    new = history.add(third)
    assert list(new.get_items()) == [(True, third), (False, first)]


def test_adding_none_from_midpoint():
    """
    Adding a blank item from midpoint in history removes any forwards items.
    """
    first = Document('http://first.com', 'First')
    second = Document('http://second.com', 'Second')
    history = History([second, first], idx=1)

    new = history.add(None)
    assert list(new.get_items()) == [(True, None), (False, first)]


def test_dump_and_load_with_blank_item():
    history = History([None, Document('http://example.com')])
    assert load_history(dump_history(history)) == history

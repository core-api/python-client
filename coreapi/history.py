from coreapi import Document
from coreapi.compat import force_bytes
import collections
import itypes
import json


HistoryItem = collections.namedtuple('HistoryItem', ['is_active', 'document'])
NavigationResult = collections.namedtuple('NavigationResult', ['document', 'history'])


class History(itypes.Object):
    def __init__(self, items=None, idx=0, max_items=None):
        self._items = itypes.List(items or [])
        self._idx = idx
        self._max_items = max_items
        if any([not isinstance(doc, Document) for doc in self._items]):
            raise ValueError('items must be a list of Document instances.')

    @property
    def max_items(self):
        return self._max_items

    @property
    def current(self):
        if not self._items:
            return None
        return self._items[self._idx]

    @property
    def is_at_most_recent(self):
        return self._idx == 0

    @property
    def is_at_oldest(self):
        return self._idx + 1 >= len(self._items)

    def get_items(self):
        for idx, item in enumerate(self._items):
            yield HistoryItem(is_active=idx == self._idx, document=item)

    def __eq__(self, other):
        return (
            isinstance(other, History) and
            self._idx == other._idx and
            self._items == other._items and
            self._max_items == other._max_items
        )

    def add(self, doc):
        if not isinstance(doc, Document):
            raise ValueError('Argument must be a Document instance.')

        new = Document(doc.url, doc.title)
        current = self.current

        # Remove any forward history past the current item.
        items = self._items[self._idx:]

        # Add the new reference if required.
        if current == new:
            pass
        elif (current is not None) and (current.url == new.url):
            items = [new] + items[1:]
        else:
            items = [new] + items

        # Truncate the history if we've reached the maximum number of items.
        items = items[:self.max_items]
        return History(items, max_items=self.max_items)

    def back(self):
        if self.is_at_oldest:
            raise ValueError('Currently at oldest point in history. Cannot navigate back.')
        idx = self._idx + 1
        doc = self._items[idx]
        history = History(self._items, idx=idx, max_items=self.max_items)
        return NavigationResult(document=doc, history=history)

    def forward(self):
        if self.is_at_most_recent:
            raise ValueError('Currently at most recent point in history. Cannot navigate forward.')
        idx = self._idx - 1
        doc = self._items[idx]
        history = History(self._items, idx=idx, max_items=self.max_items)
        return NavigationResult(document=doc, history=history)


def dump_history(history):
    history_data = {
        'items': [
            {'url': doc.url, 'title': doc.title}
            for active, doc in history.get_items()
        ],
        'idx': history._idx,
        'max_items': history.max_items
    }
    return force_bytes(json.dumps(history_data))


def load_history(bytestring):
    history_data = json.loads(bytestring.decode('utf-8'))
    items = [
        Document(item['url'], item['title'])
        for item in history_data['items']
    ]
    idx = history_data['idx']
    max_items = history_data['max_items']
    return History(items=items, idx=idx, max_items=max_items)

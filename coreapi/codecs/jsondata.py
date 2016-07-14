# coding: utf-8
from coreapi.codecs.base import BaseCodec
from coreapi.exceptions import ParseError
import collections
import json


class JSONCodec(BaseCodec):
    media_type = 'application/json'
    supports = ['data']

    def load(self, bytes, base_url=None):
        """
        Return raw JSON data.
        """
        try:
            return json.loads(bytes.decode('utf-8'), object_pairs_hook=collections.OrderedDict)
        except ValueError as exc:
            raise ParseError('Malformed JSON. %s' % exc)

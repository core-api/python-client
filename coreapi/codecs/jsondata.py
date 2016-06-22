# coding: utf-8
from coreapi.codecs.base import BaseCodec, get_json_text
from coreapi.exceptions import ParseError
import collections
import json


class JSONCodec(BaseCodec):
    media_type = 'application/json'

    def load(self, content, base_url=None, charset=None):
        """
        Return raw JSON data.
        """
        text = get_json_text(content, charset)
        try:
            return json.loads(text, object_pairs_hook=collections.OrderedDict)
        except ValueError as exc:
            raise ParseError('Malformed JSON. %s' % exc)

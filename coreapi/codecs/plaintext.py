# coding: utf-8
from coreapi.codecs.base import BaseCodec


class PlainTextCodec(BaseCodec):
    media_type = 'text/plain'

    def load(self, bytes, base_url=None):
        return bytes.decode('utf-8')

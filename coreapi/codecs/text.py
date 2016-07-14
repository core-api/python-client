# coding: utf-8
from coreapi.codecs.base import BaseCodec


class TextCodec(BaseCodec):
    media_type = 'text/*'
    supports = ['data']

    def load(self, bytes, base_url=None):
        return bytes.decode('utf-8')

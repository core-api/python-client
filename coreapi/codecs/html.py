# coding: utf-8
from coreapi.codecs.base import BaseCodec


class HTMLCodec(BaseCodec):
    media_type = 'text/html'

    def load(self, bytes, base_url=None):
        return bytes.decode('utf-8')

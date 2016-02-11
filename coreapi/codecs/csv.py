# coding: utf-8
from coreapi.codecs.base import BaseCodec


class CSVCodec(BaseCodec):
    media_type = 'text/csv'

    def load(self, bytes, base_url=None):
        return bytes.decode('utf-8')

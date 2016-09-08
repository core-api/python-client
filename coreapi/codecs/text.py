# coding: utf-8
from coreapi.codecs.base import BaseCodec


class TextCodec(BaseCodec):
    media_type = 'text/*'
    plain_data = True

    def decode(self, bytestring, **options):
        return bytestring.decode('utf-8')

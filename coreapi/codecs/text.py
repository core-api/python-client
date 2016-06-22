# coding: utf-8
from coreapi.codecs.base import BaseCodec


class TextCodec(BaseCodec):
    media_type = 'text/*'

    def load(self, content, base_url=None, charset=None):
        # RFC 2616 specifies "ISO-8859-1" as the default text charset.
        return content.decode(charset or 'iso-8859-1')

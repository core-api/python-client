import itypes


class BaseCodec(itypes.Object):
    media_type = None
    supports = []  # 'encoding', 'decoding', 'data'

    def decode(self, bytestring, **options):
        raise NotImplementedError()  # pragma: nocover

    def encode(self, document, **options):
        raise NotImplementedError()  # pragma: nocover

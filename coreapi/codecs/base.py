import itypes


class BaseCodec(itypes.Object):
    media_type = None

    def load(self, bytes, base_url=None):
        raise NotImplementedError()  # pragma: nocover

    def dump(self, document, **kwargs):
        raise NotImplementedError()  # pragma: nocover

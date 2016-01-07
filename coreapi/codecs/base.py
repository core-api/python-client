import itypes


def _mark_as_not_implemented(method):
    # Mark the method as not implemented, for the purposes for determining
    # if a codec supports encoding only, decoding only, or both.
    method.not_implemented = True
    return method


class BaseCodec(itypes.Object):
    media_type = None

    @_mark_as_not_implemented
    def load(self, bytes, base_url=None):
        raise NotImplementedError()  # pragma: nocover

    @_mark_as_not_implemented
    def dump(self, document, **kwargs):
        raise NotImplementedError()  # pragma: nocover

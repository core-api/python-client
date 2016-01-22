# coding: utf-8
import itypes


class BaseTransport(itypes.Object):
    schemes = None

    def transition(self, link, params=None, decoders=None, link_ancestors=None):
        raise NotImplementedError()  # pragma: nocover

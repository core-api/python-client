# coding: utf-8


class BaseTransport(object):
    schemes = None

    def transition(self, link, decoders, params=None, link_ancestors=None, force_codec=False):
        raise NotImplementedError()  # pragma: nocover

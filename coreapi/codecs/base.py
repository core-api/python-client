class BaseCodec(object):
    media_type = None

    # We don't implement stubs, to ensure that we can check which of these
    # two operations a codec supports. For example:
    # `if hasattr(codec, 'decode'): ...`

    # def decode(self, bytestring, **options):
    #    pass

    # def encode(self, document, **options):
    #    pass

    def get_media_types(self):
        # Fallback, while transitioning from `application/vnd.coreapi+json`
        # to simply `application/coreapi+json`.
        if hasattr(self, 'media_types'):
            return list(self.media_types)
        return [self.media_type]

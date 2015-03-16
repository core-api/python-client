# flake8: noqa
try:
    import urlparse

    def is_string(text):
        return isinstance(text, (str, unicode))
except ImportError:
    import urllib.parse as urlparse

    def is_string(text):
        return isinstance(text, str)

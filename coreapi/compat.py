# flake8: noqa
try:
    import urlparse

    string_types = (str, unicode)

    def is_string(text):
        return isinstance(text, (str, unicode))

except ImportError:
    import urllib.parse as urlparse

    string_types = (str,)

    def is_string(text):
        return isinstance(text, str)

try:  # pragma: no cover - Python 2.x
    import urlparse
    def is_string(text):
        return isinstance(text, (str, unicode))
except ImportError:  # pragma: no cover - Python 3.x
    import urllib.parse as urlparse
    def is_string(text):
        return isinstance(text, str)

# coding: utf-8
from coreapi.codecs.base import BaseCodec
from coreapi.compat import urlparse
import os
import posixpath
import shutil
import tempfile


def _safe_filename(filename):
    keepcharacters = (' ', '.', '_')
    filename = "".join(
        char for char in filename
        if char.isalnum() or char in keepcharacters
    ).strip()

    if filename == '..':
        return ''
    return filename


class DownloadCodec(BaseCodec):
    media_type = '*/*'
    supports = ['data']

    def __init__(self, download_dir=None):
        self._temporary = False
        self._download_dir = download_dir

    def __del__(self):
        if self._temporary and self._download_dir:
            shutil.rmtree(self._download_dir)

    @property
    def download_dir(self):
        if self._download_dir is None:
            self._temporary = True
            self._download_dir = tempfile.mkdtemp(prefix='temp-coreapi-download-')
        return self._download_dir

    def load(self, bytes, base_url=None):
        fd, pathname = tempfile.mkstemp(dir=self.download_dir, suffix='.download')
        file_handle = os.fdopen(fd, 'wb')
        file_handle.write(bytes)
        file_handle.close()

        filename = None
        if base_url is not None:
            url = urlparse.urlparse(base_url)
            filename = _safe_filename(posixpath.basename(url.path))
        if not filename:
            # Fallback for no filename, or empty filename generated.
            filename = os.path.basename(pathname)

        filename = os.path.join(self.download_dir, filename)
        basename, ext = os.path.splitext(filename)
        idx = 0
        while os.path.exists(filename):
            idx += 1
            filename = "%s (%d)%s" % (basename, idx, ext)

        os.rename(pathname, filename)
        return open(filename, 'rb')

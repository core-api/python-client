# coding: utf-8
from coreapi.codecs.base import BaseCodec
from coreapi.compat import urlparse
from coreapi.utils import safe_filename
import os
import posixpath
import shutil
import tempfile


def _get_available_path(path):
    basename, ext = os.path.splitext(path)
    idx = 0
    while os.path.exists(path):
        idx += 1
        path = "%s (%d)%s" % (basename, idx, ext)
    return path


def _get_filename_from_url(url):
    parsed = urlparse.urlparse(url)
    final_path_component = posixpath.basename(parsed.path.rstrip('/'))
    return safe_filename(final_path_component)


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

    def decode(self, bytestring, **options):
        filename = options.get('filename')
        base_url = options.get('base_url')

        # Write the download to a temporary .download file.
        fd, temp_path = tempfile.mkstemp(dir=self.download_dir, suffix='.download')
        file_handle = os.fdopen(fd, 'wb')
        file_handle.write(bytestring)
        file_handle.close()

        # Determine the output filename.
        output_filename = None
        if filename:
            output_filename = filename
        elif base_url is not None:
            output_filename = _get_filename_from_url(base_url)
        if not output_filename:
            # Fallback for no filename, or empty filename generated.
            filename = os.path.basename(temp_path)

        # Determine the full output path.
        output_path = os.path.join(self.download_dir, output_filename)
        output_path = _get_available_path(output_path)

        # Move the temporary download file to the final location.
        os.rename(temp_path, output_path)
        return open(output_path, 'rb')

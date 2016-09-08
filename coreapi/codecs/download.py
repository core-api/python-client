# coding: utf-8
from coreapi.codecs.base import BaseCodec
from coreapi.compat import urlparse
import cgi
import mimetypes
import os
import posixpath
import shutil
import tempfile


class DownloadedFile(tempfile._TemporaryFileWrapper):
    def __repr__(self):
        state = "closed" if self.close_called else "open"
        mode = "" if self.close_called else " '%s'" % self.file.mode
        return "<DownloadedFile '%s', %s%s>" % (self.name, state, mode)

    def __str__(self):
        return self.__repr__()


def _unique_output_path(path):
    """
    Given a path like '/a/b/c.txt'

    Return the first available filename that doesn't already exist,
    using an incrementing suffix if needed.

    For example: '/a/b/c.txt' or '/a/b/c (1).txt' or '/a/b/c (2).txt'...
    """
    basename, ext = os.path.splitext(path)
    idx = 0
    while os.path.exists(path):
        idx += 1
        path = "%s (%d)%s" % (basename, idx, ext)
    return path


def _safe_filename(filename):
    """
    Sanitize output filenames, to remove any potentially unsafe characters.
    """
    filename = os.path.basename(filename)

    keepcharacters = (' ', '.', '_', '-')
    filename = ''.join(
        char for char in filename
        if char.isalnum() or char in keepcharacters
    ).strip().strip('.')

    return filename


def _get_filename_from_content_disposition(content_disposition):
    """
    Determine an output filename based on the `Content-Disposition` header.
    """
    params = value, params = cgi.parse_header(content_disposition)

    if 'filename*' in params:
        try:
            charset, lang, filename = params['filename*'].split('\'', 2)
            filename = urlparse.unquote(filename)
            filename = filename.encode('iso-8859-1').decode(charset)
            return _safe_filename(filename)
        except (ValueError, LookupError):
            pass

    if 'filename' in params:
        filename = params['filename']
        return _safe_filename(filename)

    return None


def _get_filename_from_url(url, content_type=None):
    """
    Determine an output filename based on the download URL.
    """
    parsed = urlparse.urlparse(url)
    final_path_component = posixpath.basename(parsed.path.rstrip('/'))
    filename = _safe_filename(final_path_component)
    if filename and ('.' not in filename) and (content_type is not None):
        # If no extension exists then attempt to add one,
        # based on the content type.
        ext = mimetypes.guess_extension(content_type)
        if ext:
            filename = filename + ext
    return filename


def _get_filename(base_url=None, content_type=None, content_disposition=None):
    """
    Determine an output filename to use for the download.
    """
    filename = None
    if content_disposition:
        filename = _get_filename_from_content_disposition(content_disposition)
    if base_url and not filename:
        filename = _get_filename_from_url(base_url, content_type)
    return filename


class DownloadCodec(BaseCodec):
    """
    A codec to handle raw file downloads, such as images and other media.
    """
    media_type = '*/*'
    plain_data = True

    def __init__(self, download_dir=None):
        """
        `download_dir` - The path to use for file downloads.
        """
        self._temporary = download_dir is None
        self._download_dir = download_dir

    def __del__(self):
        if self._temporary and self._download_dir:
            shutil.rmtree(self._download_dir)

    @property
    def download_dir(self):
        if self._download_dir is None:
            self._download_dir = tempfile.mkdtemp(prefix='temp-coreapi-download-')
        return self._download_dir

    def decode(self, bytestring, **options):
        base_url = options.get('base_url')
        content_type = options.get('content_type')
        content_disposition = options.get('content_disposition')

        # Write the download to a temporary .download file.
        fd, temp_path = tempfile.mkstemp(suffix='.download')
        file_handle = os.fdopen(fd, 'wb')
        file_handle.write(bytestring)
        file_handle.close()

        # Determine the output filename.
        output_filename = _get_filename(base_url, content_type, content_disposition)
        if not output_filename:
            # Fallback if no output filename could be determined.
            output_filename = os.path.basename(temp_path)

        # Determine the full output path.
        output_path = os.path.join(self.download_dir, output_filename)
        output_path = _unique_output_path(output_path)

        # Move the temporary download file to the final location.
        os.rename(temp_path, output_path)
        output_file = open(output_path, 'rb')
        return DownloadedFile(output_file, output_path, delete=self._temporary)

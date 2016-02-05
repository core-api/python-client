# coding: utf-8
from coreapi.codecs.base import BaseCodec
import html2text
import re


class HTMLCodec(BaseCodec):
    media_type = 'text/html'

    def load(self, bytes, base_url=None):
        content = bytes.decode('utf-8')
        # HTML to text.
        converter = html2text.HTML2Text()
        converter.ignore_links = True
        converter.ignore_images = True
        content = converter.handle(content).strip()
        # Strip leading/trailing whitespace in lines.
        content = '\n'.join([line.strip() for line in content.splitlines()])
        # Remove multiple newlines
        content = re.sub(r'\n\n\n+', '\n\n', content)
        # Remove generated markdown headers
        content = re.sub('^#+ ', '', content, flags=re.MULTILINE)
        return content

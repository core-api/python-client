from __future__ import unicode_literals
from coreapi.codecs.base import BaseCodec
from coreapi.compat import urlparse
from coreapi.document import Document, Link, Array, Object, Error
import jinja2


env = jinja2.Environment(loader=jinja2.PackageLoader('coreapi', 'templates'))
env.filters.update({
    'is_link': lambda x: isinstance(x, Link),
    'is_plain_link': lambda x: x.action.upper() in ('GET', '') and not x.fields,
})


def _render_html(node, url=None, key=None, path=''):
    if key:
        path += "%s." % key

    if isinstance(node, (Document, Link)):
        url = urlparse.urljoin(url, node.url)

    if isinstance(node, Document):
        template = env.get_template('document.html')
    elif isinstance(node, Object):
        template = env.get_template('object.html')
    elif isinstance(node, Array):
        template = env.get_template('array.html')
    elif isinstance(node, Link):
        template = env.get_template('link.html')
    elif isinstance(node, Error):
        template = env.get_template('error.html')
    elif node is None or isinstance(node, bool):
        value = {True: 'true', False: 'false', None: 'null'}[node]
        return "<code>%s</code>" % value
    elif isinstance(node, (float, int)):
        return "<code>%s</code>" % node
    else:
        return "<span>%s</span>" % node.replace('\n', '<br/>')

    return template.render(node=node, render=_render_html, url=url, key=key, path=path)


class CoreHTMLCodec(BaseCodec):
    media_type = 'text/html'

    def dump(self, document, extra_css=None, **kwargs):
        template = env.get_template('index.html')
        return template.render(document=document, render=_render_html, extra_css=extra_css)

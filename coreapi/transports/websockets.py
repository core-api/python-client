from coreapi.codecs import negotiate_decoder, default_decoders
from coreapi.compat import force_bytes
from coreapi.transports.base import BaseTransport
from websocket import create_connection
from websocket._exceptions import WebSocketConnectionClosedException
import json
import jsonpatch


def _get_headers_and_body(content):
    head, body = content.split('\n\n', 1)
    key_value_pairs = [line.split(':', 1) for line in head.splitlines()]
    headers = dict([
        (key.strip().lower(), value.strip())
        for key, value in key_value_pairs
    ])
    return (headers, body)


def _decode_content(headers, content, decoders=None, base_url=None):
    content_type = headers.get('content-type')
    codec = negotiate_decoder(content_type, decoders=decoders)
    return codec.load(content, base_url=base_url)


def _diff_content(heaaders, body, diff):
    patch = jsonpatch.JsonPatch.from_string(diff)
    previous_data = json.loads(body)
    next_data = jsonpatch.apply_patch(previous_data, patch)
    return json.dumps(next_data)


def _generate_request(decoders=None):
    # TODO: Include User-Agent, X-Accept-Diff
    if decoders is None:
        decoders = default_decoders

    accept = ', '.join([decoder.media_type for decoder in decoders])
    return 'Accept: %s\n\n' % accept


class WebSocketsTransport(BaseTransport):
    schemes = ['ws', 'wss']

    def transition(self, link, params=None, decoders=None, link_ancestors=None):
        url = link.url
        connection = create_connection(url)
        request = _generate_request(decoders)
        connection.send(request)
        content = connection.recv()
        headers, body = _get_headers_and_body(content)
        yield _decode_content(headers, body, decoders=decoders, base_url=url)
        while True:
            try:
                diff = connection.recv()
            except WebSocketConnectionClosedException:
                return
            body = _diff_content(headers, body, diff)
            patch = jsonpatch.JsonPatch.from_string(diff)
            body = json.dumps(jsonpatch.apply_patch(json.loads(body), patch))
            yield _decode_content(headers, body, decoders=decoders, base_url=url)

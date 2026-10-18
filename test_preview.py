"""Preview transport must preserve the scientific payload and reject bad input."""
import gzip
import http.client
import json
import threading
from http.server import ThreadingHTTPServer

import pytest
from preview import Handler, _encoded_workspace, accepts_gzip, response_bytes
from scenario_workspace import CATALOG, build_workspace


@pytest.mark.parametrize('header,expected', [
    ('', False), ('br, gzip', True), ('GZip;q=0.5', True),
    ('gzip;q=0, *;q=1', False), ('*;q=.5', True),
    ('gzip;q=oops', False), ('gzip;q=2', False), ('br', False),
])
def test_compression_negotiation(header, expected):
    assert accepts_gzip(header) is expected


@pytest.mark.parametrize('spec', CATALOG, ids=lambda spec: spec['id'])
def test_plain_and_compressed_payload_match_engine(spec):
    settings = {'scenario': spec['id']}
    expected = json.loads(json.dumps(build_workspace(settings)))
    plain, encoding = response_bytes(settings)
    compressed, gzip_encoding = response_bytes(settings, compressed=True)
    assert encoding is None
    assert gzip_encoding == 'gzip'
    assert json.loads(plain) == json.loads(gzip.decompress(compressed)) == expected
    assert len(compressed) < len(plain)


def test_cache_is_canonical_bounded_and_validation_is_not_bypassed():
    _encoded_workspace.cache_clear()
    first = response_bytes({'scenario': 'blackhole', 'mass': 10, 'distance': 1})
    second = response_bytes({'distance': 1.0, 'mass': 10.0, 'scenario': 'blackhole', 'unused': 1})
    assert first is second
    assert _encoded_workspace.cache_info().hits == 1
    with pytest.raises(ValueError):
        response_bytes({'scenario': 'blackhole', 'mass': True})
    # Different response representations cannot contaminate each other.
    assert response_bytes({'scenario': 'blackhole'}, True)[1] == 'gzip'
    assert response_bytes({'scenario': 'blackhole'}, False)[1] is None
    for hours in range(2, 25):
        response_bytes({'scenario': 'earth_rotation', 'hours': hours})
    assert _encoded_workspace.cache_info().currsize == 16


@pytest.fixture
def server():
    class QuietHandler(Handler):
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server.server_port
    server.shutdown()
    server.server_close()
    thread.join()


def test_real_http_negotiation_lengths_and_error_response(server):
    conn = http.client.HTTPConnection('127.0.0.1', server)
    settings = {'scenario': 'sirius', 'distance': 5}
    for header, encoding in [('gzip', 'gzip'), ('gzip;q=0', None)]:
        conn.request('POST', '/api/experiment', json.dumps(settings),
                     {'Content-Type': 'application/json', 'Accept-Encoding': header})
        response = conn.getresponse()
        body = response.read()
        assert response.status == 200
        assert response.getheader('Content-Encoding') == encoding
        assert response.getheader('Vary') == 'Accept-Encoding'
        assert response.getheader('Cache-Control') == 'no-store'
        assert int(response.getheader('Content-Length')) == len(body)
        assert json.loads(gzip.decompress(body) if encoding else body) == json.loads(json.dumps(build_workspace(settings)))
    conn.request('POST', '/api/experiment', '{"scenario":"unknown"}',
                 {'Accept-Encoding': 'gzip'})
    response = conn.getresponse()
    assert response.status == 400
    assert response.getheader('Content-Encoding') is None
    assert json.loads(response.read())['error']
    conn.close()

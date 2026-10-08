"""Exercise real HTTP requests so parsed request headers cannot be mocked away."""
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

spec = importlib.util.spec_from_file_location(
    'dj_http', Path(__file__).resolve().parents[1] / 'media/ai-dj/service.py'
)
dj = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dj)


class DjHttpTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), dj.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_health_and_prepare_use_real_http_headers(self):
        with urllib.request.urlopen(self.url + '/health', timeout=5) as response:
            self.assertTrue(json.load(response)['ok'])
        with tempfile.TemporaryDirectory() as folder:
            audio = Path(folder) / 'voice.wav'
            audio.write_bytes(b'audio')
            with patch.object(dj, 'ollama_script', return_value='Next track.'), \
                    patch.object(dj, 'make_audio', return_value=audio), \
                    patch.object(dj, 'cleanup'):
                request = urllib.request.Request(
                    self.url + '/dj/prepare',
                    data=b'{"nextTrack":{"title":"Song"}}',
                    headers={'Content-Type': 'application/json'},
                )
                with urllib.request.urlopen(request, timeout=5) as response:
                    result = json.load(response)
                self.assertEqual(result['script'], 'Next track.')
                self.assertEqual(result['audioFile'], audio.as_uri())

    def test_invalid_json_and_oversized_requests_fail_before_generating_audio(self):
        with patch.object(dj, 'make_audio') as audio:
            cases = [(b'[]', 400), (b'broken', 400), (b'\xff', 400), (b'x' * 65537, 413)]
            for body, expected in cases:
                with self.subTest(body_length=len(body), expected=expected):
                    request = urllib.request.Request(self.url + '/dj/prepare', data=body)
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        urllib.request.urlopen(request, timeout=5)
                    self.assertEqual(error.exception.code, expected)
            audio.assert_not_called()

    def test_generation_failure_is_reported_as_server_error(self):
        with patch.object(dj, 'ollama_script', side_effect=RuntimeError('model unavailable')):
            request = urllib.request.Request(self.url + '/dj/prepare', data=b'{}')
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(request, timeout=5)
            self.assertEqual(error.exception.code, 500)
            self.assertIn('model unavailable', json.load(error.exception)['error'])

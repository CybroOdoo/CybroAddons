# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import contextlib
import importlib.util
import json
import os
import shutil
import signal
import socket
import sys
import tempfile
import threading
import time
from unittest import skipUnless
from unittest.mock import MagicMock, patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.meeting_transcription_summary.tools import stt_client, stt_worker

# Only the local speech engines need numpy (faster-whisper installs it); the module
# and the other engines work without it, so these tests skip where it is missing
HAS_NUMPY = importlib.util.find_spec('numpy') is not None
NO_NUMPY = "numpy is not installed"


class SttSocketCase(TransactionCase):
    """A private socket for the speech worker, so the tests never reach the server's real one."""

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp(prefix='stt')
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.socket_path = os.path.join(self.tmp, 'worker.sock')
        self.startPatcher(patch.object(stt_client, 'SOCKET_PATH', self.socket_path))
        self.startPatcher(patch.object(stt_client, 'START_LOCK_PATH', os.path.join(self.tmp, 'worker.lock')))
        self.scheduler = stt_worker.Scheduler()

    def _listen(self, serve=None):
        """Serve the socket in a thread, by default with the worker's own connection handler."""
        serve = serve or (lambda conn: stt_worker.serve_connection(conn, self.scheduler))
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(self.socket_path)
        server.listen(8)
        server.settimeout(0.1)
        stop = threading.Event()

        def loop():
            while not stop.is_set():
                try:
                    conn, _addr = server.accept()
                except TimeoutError:
                    continue
                except OSError:
                    return
                threading.Thread(target=serve, args=(conn,), daemon=True).start()

        thread = threading.Thread(target=loop, daemon=True)
        thread.start()

        def close():
            stop.set()
            thread.join(5)
            server.close()

        self.addCleanup(close)


@tagged('post_install', '-at_install')
class TestSttClientRequests(SttSocketCase):
    """Requests to the shared worker, answered by the worker's real connection handler."""

    def test_transcribe_through_worker(self):
        received = []

        def handle(header, audio):
            received.append((header, audio))
            return {'text': 'Hello Odoo', 'language': 'en', 'language_probability': 0.9}

        self.startPatcher(patch.object(stt_worker, 'handle', side_effect=handle))
        self._listen()
        result = stt_client.transcribe_with_info(
            b'audio', 'whisper', language='en', keywords=['Odoo'], prompt='Earlier.', workers=2)
        self.assertEqual(result['text'], 'Hello Odoo')
        self.assertEqual(result['language'], 'en')
        self.assertEqual(result['language_probability'], 0.9)
        self.assertIsInstance(result['queue_seconds'], float)
        self.assertIsInstance(result['stt_seconds'], float)
        header, audio = received[0]
        self.assertEqual(audio, b'audio')
        self.assertEqual(header['size'], 5)
        self.assertEqual(header['keywords'], ['Odoo'])
        self.assertEqual(header['prompt'], 'Earlier.')
        self.assertEqual(header['workers'], 2)
        self.assertEqual(stt_client.transcribe(b'audio', 'whisper'), 'Hello Odoo', "only the text")

    def test_empty_reply_defaults(self):
        self.startPatcher(patch.object(stt_worker, 'handle', return_value={'text': None}))
        self._listen()
        result = stt_client.transcribe_with_info(b'audio', 'whistle')
        self.assertEqual(result['text'], '')
        self.assertIsNone(result['language'])
        self.assertEqual(result['language_probability'], 0.0)

    def test_engine_not_installed(self):
        self.startPatcher(patch.object(stt_worker, 'handle', side_effect=ImportError('No module named needle')))
        self._listen()
        with self.assertRaisesRegex(stt_client.SttWorkerUnavailable, 'not_installed'):
            stt_client.transcribe(b'audio', 'whistle')

    def test_worker_error(self):
        self.startPatcher(patch.object(stt_worker, 'handle', side_effect=ValueError('bad audio')))
        self._listen()
        with self.assertRaises(stt_client.SttWorkerError) as caught:
            stt_client.transcribe(b'audio', 'whisper')
        self.assertNotIsInstance(caught.exception, stt_client.SttWorkerUnavailable)
        self.assertIn('bad audio', str(caught.exception))

    def test_busy_worker(self):
        handle = self.startPatcher(patch.object(stt_worker, 'handle'))
        self._listen()
        self.assertTrue(self.scheduler.acquire(0, engine='whisper'), "another caption is transcribing")
        with self.assertRaisesRegex(stt_client.SttWorkerUnavailable, 'busy'):
            stt_client.transcribe(b'audio', 'whisper', lock_timeout=0)
        handle.assert_not_called()

    def test_only_if_cold(self):
        handle = self.startPatcher(patch.object(stt_worker, 'handle', return_value={'text': ''}))
        self._listen()
        with patch.dict(stt_worker._whisper_models, {'small': (object(), 1)}, clear=True):
            header = stt_client._header('whisper', 'auto', 'small', [], lock_timeout=0)
            self.assertIsNone(stt_client._request(header, b'', only_if_cold=True), "already loaded")
            handle.assert_not_called()
            header = stt_client._header('whisper', 'auto', 'small', [], lock_timeout=0, workers=2)
            self.assertIsNotNone(stt_client._request(header, b'', only_if_cold=True),
                                 "loaded again for another number of workers")
            handle.assert_called_once()

    def test_retries_worker_exiting_as_it_connects(self):
        self.startPatcher(patch.object(stt_worker, 'handle', return_value={'text': 'Hi'}))
        connections = []

        def serve(conn):
            connections.append(conn)
            if len(connections) == 1:
                conn.close()  # idle worker exiting
            else:
                stt_worker.serve_connection(conn, self.scheduler)

        self._listen(serve)
        self.assertEqual(stt_client.transcribe(b'audio', 'whisper'), 'Hi')
        self.assertEqual(len(connections), 2)

    def test_worker_does_not_answer(self):
        self._listen(lambda conn: conn.close())
        with self.assertRaisesRegex(stt_client.SttWorkerError, 'does not answer'):
            stt_client.transcribe(b'audio', 'whisper')

    def test_connection_lost_during_request(self):
        def serve(conn):
            conn.sendall(json.dumps({'pid': 1, 'loaded': []}).encode() + b'\n')
            conn.recv(65536)
            conn.close()

        self._listen(serve)
        with self.assertRaisesRegex(stt_client.SttWorkerError, 'failed'):
            stt_client.transcribe(b'audio', 'whisper')

    def test_stuck_worker_is_killed(self):
        held = []

        def serve(conn):
            held.append(conn)
            conn.sendall(json.dumps({'pid': 12345, 'loaded': [['whisper', 'small', 1]]}).encode() + b'\n')

        self.addCleanup(lambda: [conn.close() for conn in held])
        self._listen(serve)
        self.startPatcher(patch.object(stt_client, 'REQUEST_TIMEOUT', 0.3))
        kill = self.startPatcher(patch.object(stt_client, '_kill'))
        with self.assertRaisesRegex(stt_client.SttWorkerError, 'timed out'):
            stt_client.transcribe(b'audio', 'whisper', lock_timeout=0)
        kill.assert_called_once_with(12345)

    def test_kill(self):
        with patch.object(os, 'kill') as kill:
            stt_client._kill(None)
            kill.assert_not_called()
            stt_client._kill(12345)
            kill.assert_called_once_with(12345, signal.SIGKILL)
        with patch.object(os, 'kill', side_effect=ProcessLookupError):
            stt_client._kill(12345)  # already gone

    @skipUnless(HAS_NUMPY, NO_NUMPY)
    def test_silent_wav(self):
        samples = stt_worker.decode_wav(stt_client._silent_wav(seconds=2))
        self.assertEqual(len(samples), 32000)
        self.assertFalse(samples.any())

    def test_warm_up(self):
        def run_now(target, name, daemon):
            return MagicMock(start=target)

        self.startPatcher(patch.object(stt_client.threading, 'Thread', side_effect=run_now))
        with patch.object(stt_client, '_request') as request:
            stt_client.warm_up('whisper', model='base', workers=2)
        header = request.call_args.args[0]
        self.assertEqual((header['model'], header['workers'], header['beam_size'], header['lock_timeout']),
                         ('base', 2, 1, 0), "greedy, and never waits for a turn")
        self.assertTrue(request.call_args.kwargs['only_if_cold'])
        logger = self.startPatcher(patch.object(stt_client, '_logger'))
        with patch.object(stt_client, '_request', side_effect=stt_client.SttWorkerUnavailable('busy')):
            stt_client.warm_up('whistle')
        logger.info.assert_not_called()
        with patch.object(stt_client, '_request', side_effect=stt_client.SttWorkerError('down')):
            stt_client.warm_up('whistle')
        logger.info.assert_called_once()


@tagged('post_install', '-at_install')
class TestSttClientStart(SttSocketCase):
    """Starting the shared worker when none runs."""

    def test_starts_worker_when_none_runs(self):
        with open(self.socket_path, 'w') as f:
            f.write('left by a killed worker')
        self.startPatcher(patch.object(stt_worker, 'handle', return_value={'text': 'Started'}))
        proc = MagicMock()

        def popen(*args, **kwargs):
            self._listen()
            return proc

        with patch.object(stt_client.subprocess, 'Popen', side_effect=popen) as Popen:
            self.assertEqual(stt_client.transcribe(b'audio', 'whisper'), 'Started')
            self.assertEqual(stt_client.transcribe(b'audio', 'whisper'), 'Started')
        Popen.assert_called_once()
        self.assertEqual(Popen.call_args.args[0], [sys.executable, stt_client.WORKER_PATH, self.socket_path])
        self.assertTrue(Popen.call_args.kwargs['start_new_session'])
        self.assertEqual(Popen.call_args.kwargs['env']['NEEDLE_TELEMETRY'], '0')

    def test_worker_exits_at_start(self):
        proc = MagicMock(returncode=1)
        proc.poll.return_value = 1
        with patch.object(stt_client.subprocess, 'Popen', return_value=proc), \
                self.assertRaisesRegex(stt_client.SttWorkerError, r'exited at start \(code 1\)'):
            stt_client.transcribe(b'audio', 'whisper')

    def test_worker_never_listens(self):
        proc = MagicMock()
        proc.poll.return_value = None
        self.startPatcher(patch.object(stt_client, 'START_TIMEOUT', 0.1))
        with patch.object(stt_client.subprocess, 'Popen', return_value=proc), \
                self.assertRaisesRegex(stt_client.SttWorkerError, 'did not start'):
            stt_client.transcribe(b'audio', 'whisper')
        proc.kill.assert_called_once()

    def test_unreachable(self):
        self.startPatcher(patch.object(stt_client, 'START_LOCK_PATH', os.path.join(self.tmp, 'missing', 'lock')))
        with self.assertRaisesRegex(stt_client.SttWorkerError, 'unreachable'):
            stt_client.transcribe(b'audio', 'whisper')

    def test_real_worker_process(self):
        """The worker script itself: answers, reports errors, removes its socket when stopped."""
        with self.assertRaisesRegex(stt_client.SttWorkerError, "unknown engine 'nope'"):
            stt_client.transcribe(b'audio', 'nope')
        with stt_client._connect() as sock:
            hello = stt_client._read_line(sock, time.monotonic() + 5)
        self.addCleanup(stt_client._kill, hello['pid'])  # should the test fail before it stops
        self.assertEqual(hello['loaded'], [], "no model was loaded")
        os.kill(hello['pid'], signal.SIGTERM)
        # at once, even when the signal lands on a connection thread instead of the main one
        deadline = time.monotonic() + 5
        while os.path.exists(self.socket_path) and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertFalse(os.path.exists(self.socket_path), "the stopped worker removes its socket")
        with contextlib.suppress(ChildProcessError):
            os.waitpid(hello['pid'], 0)  # reap it


@tagged('post_install', '-at_install')
class TestSttClientJobs(TransactionCase):
    """Recording jobs: the files a job starts from, its status, and cancelling it."""

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp(prefix='stt')
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.job_dir = os.path.join(self.tmp, 'job')

    def _start(self, request=None, filename='Meeting.MP3', pid=4242):
        with patch.object(stt_client.subprocess, 'Popen', return_value=MagicMock(pid=pid)) as Popen:
            stt_client.start_job(self.job_dir, request or {'engine': 'grok', 'api_key': 'secret'},
                                 b'recording', filename)
        return Popen

    def _path(self, name):
        return os.path.join(self.job_dir, name)

    def test_start_job(self):
        os.makedirs(self.job_dir)
        with open(self._path('result.json'), 'w') as f:
            f.write('{"error": "earlier attempt"}')
        Popen = self._start()
        self.assertFalse(os.path.exists(self._path('result.json')), "leftovers removed")
        with open(self._path('audio.mp3'), 'rb') as f:
            self.assertEqual(f.read(), b'recording')
        with open(self._path('request.json')) as f:
            self.assertEqual(json.load(f), {'engine': 'grok', 'api_key': 'secret', 'audio': 'audio.mp3'})
        self.assertEqual(os.stat(self._path('request.json')).st_mode & 0o777, 0o600, "holds the API key")
        with open(self._path('pid')) as f:
            self.assertEqual(f.read(), '4242')
        self.assertEqual(Popen.call_args.args[0], [sys.executable, stt_client.JOB_PATH, self.job_dir])
        self.assertTrue(Popen.call_args.kwargs['start_new_session'])
        self.assertEqual(stt_client.job_status(self.job_dir), ('running', None))

    def test_start_job_without_extension(self):
        self._start(filename=None)
        self.assertTrue(os.path.exists(self._path('audio.bin')))

    def test_job_status(self):
        self._start()
        with open(self._path('result.json'), 'w') as f:
            json.dump({'text': 'Hello', 'duration': 3.0}, f)
        self.assertEqual(stt_client.job_status(self.job_dir), ('done', {'text': 'Hello', 'duration': 3.0}))
        with open(self._path('result.json'), 'w') as f:
            f.write('{"text": ')
        self.assertEqual(stt_client.job_status(self.job_dir), ('failed', 'unreadable job result'))
        os.unlink(self._path('result.json'))
        old = time.time() - stt_client.JOB_STALE_SECONDS - 10
        os.utime(self._path('heartbeat'), (old, old))
        status, reason = stt_client.job_status(self.job_dir)
        self.assertEqual(status, 'failed')
        self.assertIn(self._path('job.log'), reason)
        os.unlink(self._path('heartbeat'))
        self.assertEqual(stt_client.job_status(self.job_dir), ('failed', 'the transcription job was lost'))

    def test_cancel_running_job(self):
        self._start()
        with patch.object(os, 'kill') as kill:
            stt_client.cancel_job(self.job_dir)
        kill.assert_called_once_with(4242, signal.SIGTERM)
        self.assertFalse(os.path.exists(self.job_dir))

    def test_cancel_finished_job(self):
        self._start()
        with open(self._path('result.json'), 'w') as f:
            json.dump({'text': 'Hello'}, f)
        with patch.object(os, 'kill') as kill:
            stt_client.cancel_job(self.job_dir)
        kill.assert_not_called()  # its pid may belong to another process by now
        self.assertFalse(os.path.exists(self.job_dir))

    def test_real_job_process(self):
        """The job script itself runs detached and reports a failed request in its result."""
        stt_client.start_job(self.job_dir, {'engine': 'grok'}, b'recording', 'meeting.mp3')
        deadline = time.monotonic() + 60
        while stt_client.job_status(self.job_dir)[0] == 'running' and time.monotonic() < deadline:
            time.sleep(0.1)
        self.assertEqual(stt_client.job_status(self.job_dir), ('done', {'error': "'api_key'"}))
        with open(self._path('pid')) as f, contextlib.suppress(ChildProcessError):
            os.waitpid(int(f.read()), 0)  # reap it

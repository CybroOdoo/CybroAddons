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

import json
import os
import resource
import shutil
import sys
import tempfile
import threading
import types
from unittest.mock import MagicMock, patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.meeting_transcription_summary.tools import stt_job


@tagged('post_install', '-at_install')
class TestSttJob(TransactionCase):
    """The detached recording job, run in-process with the engines faked."""

    def setUp(self):
        super().setUp()
        self.job_dir = tempfile.mkdtemp(prefix='stt_job')
        self.addCleanup(shutil.rmtree, self.job_dir, True)
        with open(os.path.join(self.job_dir, 'audio.mp3'), 'wb') as f:
            f.write(b'recording')

    def _result(self):
        with open(os.path.join(self.job_dir, 'result.json')) as f:
            return json.load(f)

    def _main(self, request, run=None):
        with open(os.path.join(self.job_dir, 'request.json'), 'w') as f:
            json.dump(request, f)
        with patch.object(sys, 'argv', ['stt_job.py', self.job_dir]), \
                patch.object(resource, 'getrlimit', return_value=(100, 200)), \
                patch.object(resource, 'setrlimit') as setrlimit, \
                patch.object(stt_job, 'run', **(run or {})):
            stt_job.main()
        return setrlimit

    def test_write_json(self):
        stt_job.write_json(self.job_dir, 'result.json', {'text': 'Hello'})
        self.assertEqual(self._result(), {'text': 'Hello'})
        self.assertFalse(os.path.exists(os.path.join(self.job_dir, 'result.json.tmp')))

    def test_heartbeat(self):
        stop = threading.Event()
        thread = threading.Thread(target=stt_job.heartbeat, args=(self.job_dir, stop))
        thread.start()
        path = os.path.join(self.job_dir, 'heartbeat')
        for _i in range(500):
            if os.path.exists(path):
                break
            stop.wait(0.01)
        stop.set()
        thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertTrue(os.path.exists(path))
        # cancelled: the directory is gone, the heartbeat stops by itself
        stt_job.heartbeat(os.path.join(self.job_dir, 'gone'), threading.Event())

    def test_run_grok(self):
        grok_stt = types.ModuleType('grok_stt')
        grok_stt.transcribe = MagicMock(return_value={'duration': 12.5})
        grok_stt.speaker_transcript = MagicMock(return_value='Speaker 1: Hello')
        request = {'engine': 'grok', 'audio': 'audio.mp3', 'api_key': 'secret', 'language': 'en',
                   'keywords': ['Odoo']}
        with patch.dict(sys.modules, {'grok_stt': grok_stt}):
            result = stt_job.run(self.job_dir, request)
        self.assertEqual(result, {'text': 'Speaker 1: Hello', 'duration': 12.5})
        args, kwargs = grok_stt.transcribe.call_args
        self.assertEqual(args, (b'recording', 'secret'))
        self.assertEqual(kwargs['filename'], 'audio.mp3')
        self.assertEqual(kwargs['keywords'], ['Odoo'])
        self.assertTrue(kwargs['diarize'])

    def test_run_whisper(self):
        stt_worker = types.ModuleType('stt_worker')
        stt_worker.patch_faster_whisper_av = MagicMock()
        stt_worker.transcribe_whisper = MagicMock(return_value={'text': 'Hello', 'duration': 3.0, 'language': 'en'})
        request = {'engine': 'whisper', 'audio': 'audio.mp3', 'language': 'auto', 'main_language': 'en'}
        with patch.dict(sys.modules, {'stt_worker': stt_worker}):
            result = stt_job.run(self.job_dir, request)
        self.assertEqual(result, {'text': 'Hello', 'duration': 3.0})
        stt_worker.patch_faster_whisper_av.assert_called_once()
        stt_worker.transcribe_whisper.assert_called_once_with(
            b'recording', 'auto', 'small', [], beam_size=5, main_language='en')

    def test_main_writes_result(self):
        request = {'engine': 'whisper', 'audio': 'audio.mp3'}
        setrlimit = self._main(request, {'return_value': {'text': 'Hello', 'duration': 3.0}})
        self.assertEqual(self._result(), {'text': 'Hello', 'duration': 3.0})
        setrlimit.assert_called_once_with(resource.RLIMIT_AS, (200, 200))

    def test_main_engine_not_installed(self):
        self._main({'engine': 'whisper', 'audio': 'audio.mp3'},
                   {'side_effect': ImportError('No module named faster_whisper')})
        self.assertEqual(self._result(), {'error': 'not_installed: No module named faster_whisper'})

    def test_main_failure(self):
        with self.assertLogs('stt_job', 'ERROR'):
            self._main({'engine': 'grok', 'audio': 'audio.mp3'}, {'side_effect': RuntimeError('API down')})
        self.assertEqual(self._result(), {'error': 'API down'})
        with self.assertLogs('stt_job', 'ERROR'):
            self._main({'engine': 'grok', 'audio': 'audio.mp3'}, {'side_effect': RuntimeError()})
        self.assertEqual(self._result(), {'error': 'RuntimeError()'}, "an empty message is still reported")

    def test_main_cancelled_meanwhile(self):
        def run(job_dir, request):
            shutil.rmtree(job_dir)
            return {'text': 'Hello'}

        self._main({'engine': 'grok', 'audio': 'audio.mp3'}, {'side_effect': run})
        self.assertFalse(os.path.exists(self.job_dir))

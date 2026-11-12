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

import importlib.metadata
import importlib.util
import io
import json
import os
import socket
import sys
import threading
import time
import types
import wave
from types import SimpleNamespace
from unittest import skipUnless
from unittest.mock import MagicMock, patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.meeting_transcription_summary.tools import stt_client, stt_worker

# Only the local speech engines need numpy (faster-whisper installs it); the module
# and the other engines work without it, so these tests skip where it is missing
HAS_NUMPY = importlib.util.find_spec('numpy') is not None
NO_NUMPY = "numpy is not installed"


@tagged('post_install', '-at_install')
class TestSpeechWorkerScheduler(TransactionCase):
    """Turns of the shared speech worker: how many captions are transcribed at once."""

    def test_one_caption_at_a_time_by_default(self):
        scheduler = stt_worker.Scheduler()
        self.assertTrue(scheduler.acquire(0, engine='whisper'))
        self.assertEqual(scheduler.idle_seconds(), 0.0)
        self.assertFalse(scheduler.acquire(0, engine='whisper'), "a second caption waits for the first")
        scheduler.release('whisper')
        self.assertTrue(scheduler.acquire(0, engine='whisper'))

    def test_workers_transcribe_captions_together(self):
        scheduler = stt_worker.Scheduler()
        self.assertTrue(scheduler.acquire(0, workers=2, engine='whisper'))
        self.assertTrue(scheduler.acquire(0, workers=2, engine='whisper'))
        self.assertFalse(scheduler.acquire(0, workers=2, engine='whisper'), "a third waits for a free worker")
        scheduler.release('whisper')
        self.assertTrue(scheduler.acquire(0, workers=2, engine='whisper'))

    def test_whistle_one_at_a_time(self):
        scheduler = stt_worker.Scheduler()
        self.assertTrue(scheduler.acquire(0, workers=2, engine='whistle'))
        self.assertFalse(scheduler.acquire(0, workers=2, engine='whistle'))
        self.assertTrue(scheduler.acquire(0, workers=2, engine='whisper'), "Whisper may run beside it")
        scheduler.release('whistle')
        scheduler.release('whisper')
        self.assertTrue(scheduler.acquire(0, workers=2, engine='whistle'))

    def test_waiting_caption_gets_the_next_turn(self):
        scheduler = stt_worker.Scheduler()
        self.assertTrue(scheduler.acquire(0, engine='whisper'))
        result = {}
        thread = threading.Thread(target=lambda: result.update(got=scheduler.acquire(5, engine='whisper')))
        thread.start()
        deadline = time.monotonic() + 5
        while not scheduler._waiting and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(scheduler._waiting, 1)
        scheduler.release('whisper')
        thread.join(5)
        self.assertTrue(result['got'])

    def test_request_workers(self):
        self.assertEqual(stt_worker.request_workers({}), 1)
        self.assertEqual(stt_worker.request_workers({'workers': 3}), 3)
        self.assertEqual(stt_worker.request_workers({'workers': 0}), 1)
        self.assertEqual(stt_worker.request_workers({'workers': 'many'}), 1)

    def test_header_carries_workers(self):
        self.assertEqual(stt_client._header('whisper', 'en', 'small', [])['workers'], 1)
        self.assertEqual(stt_client._header('whisper', 'en', 'small', [], workers=2)['workers'], 2)

    def test_missing_package(self):
        def distribution(name):
            if name != 'faster-whisper':
                raise importlib.metadata.PackageNotFoundError(name)

        with patch.object(importlib.metadata, 'distribution', side_effect=distribution):
            self.assertIsNone(stt_client.missing_package('whisper'))
            self.assertEqual(stt_client.missing_package('whistle'), 'cactus-needle')
            self.assertIsNone(stt_client.missing_package('grok'), "a cloud engine needs no package")


def _wav(samples, rate=16000, channels=1):
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b''.join(int(s).to_bytes(2, 'little', signed=True) for s in samples))
    return buf.getvalue()


def _segment(text, no_speech=0.01, logprob=-0.2, ratio=1.2):
    return SimpleNamespace(text=text, no_speech_prob=no_speech, avg_logprob=logprob, compression_ratio=ratio)


class FakeWhisperModel:
    supported_languages = ['en', 'de', 'nl']

    def __init__(self, segments, detected=('de', 0.9), probability=0.8):
        self.segments = segments
        self.detected = detected
        self.probability = probability
        self.detect_calls = 0
        self.calls = []

    def detect_language(self, samples):
        self.detect_calls += 1
        return self.detected[0], self.detected[1], []

    def transcribe(self, audio, **options):
        self.calls.append((audio, options, isinstance(audio, str) and os.path.exists(audio)))
        info = SimpleNamespace(language=options['language'] or 'en', language_probability=self.probability,
                               duration=2.0)
        return iter(self.segments), info


@tagged('post_install', '-at_install')
class TestSpeechWorkerText(TransactionCase):
    """Decoding the audio and cleaning up what the engines return."""

    @skipUnless(HAS_NUMPY, NO_NUMPY)
    def test_decode_wav(self):
        self.assertIsNone(stt_worker.decode_wav(b'OggS...'), "not a WAV")
        self.assertIsNone(stt_worker.decode_wav(_wav([0, 0], rate=8000)), "not 16 kHz")
        self.assertEqual(list(stt_worker.decode_wav(_wav([16384, -32768]))), [0.5, -1.0])
        self.assertEqual(list(stt_worker.decode_wav(_wav([16384, 0], channels=2))), [0.25], "stereo is mixed down")

    def test_clean_text(self):
        self.assertEqual(stt_worker.clean_text(' [Music]  Hello (laughs)   there ♪ '), 'Hello there')
        self.assertEqual(stt_worker.clean_text('[Music]'), '')
        self.assertEqual(stt_worker.clean_text('Thank you.'), '', "a typical hallucination")
        self.assertEqual(stt_worker.clean_text('Thank you.', keep_known=True), 'Thank you.')
        self.assertEqual(stt_worker.clean_text('Thank you, Anna.'), 'Thank you, Anna.')

    def test_segment_quality(self):
        self.assertTrue(stt_worker.is_reliable(_segment('Hello')))
        self.assertFalse(stt_worker.is_reliable(_segment('')))
        self.assertFalse(stt_worker.is_reliable(_segment('Hello', no_speech=0.7)))
        self.assertFalse(stt_worker.is_reliable(_segment('Hello', logprob=-1.2)))
        self.assertFalse(stt_worker.is_reliable(_segment('Hello', ratio=2.5)))
        self.assertTrue(stt_worker.is_confident(_segment('Hello')))
        self.assertFalse(stt_worker.is_confident(_segment('Hello', logprob=-0.6)))
        self.assertFalse(stt_worker.is_confident(_segment('Hello', no_speech=0.3)))

    def test_read_exact(self):
        self.assertEqual(stt_worker.read_exact(io.BytesIO(b'abcdef'), 4), b'abcd')
        with self.assertRaises(EOFError):
            stt_worker.read_exact(io.BytesIO(b'ab'), 4)

    def test_scheduler_idle_time(self):
        scheduler = stt_worker.Scheduler()
        scheduler.last_activity -= 10
        self.assertGreaterEqual(scheduler.idle_seconds(), 10)
        scheduler.touch()
        self.assertLess(scheduler.idle_seconds(), 10)


@tagged('post_install', '-at_install')
class TestSpeechWorkerWhisper(TransactionCase):
    """Whisper transcription with a fake model: options, language choice and segment filtering."""

    def _transcribe(self, model, audio=None, language='auto', **kwargs):
        with patch.object(stt_worker, 'whisper_model', return_value=model) as whisper_model:
            result = stt_worker.transcribe_whisper(
                audio or stt_client._silent_wav(), language, 'small', kwargs.pop('keywords', []), **kwargs)
        whisper_model.assert_called_once_with('small', kwargs.get('workers', 1))
        return result

    @skipUnless(HAS_NUMPY, NO_NUMPY)
    def test_detects_language_once(self):
        model = FakeWhisperModel([
            _segment(' Hallo zusammen. '), _segment('invented', no_speech=0.9),
            _segment('garbage', logprob=-1.5), _segment('repeated repeated', ratio=3.0), _segment('Los geht es.'),
        ])
        result = self._transcribe(model, keywords=['Odoo', 'Ash'], prompt='Earlier.', beam_size=1)
        self.assertEqual(model.detect_calls, 1)
        _audio, options, _path = model.calls[0]
        self.assertEqual(options['language'], 'de', "the detection is handed over, not run again")
        self.assertEqual(options['hotwords'], 'Odoo Ash')
        self.assertEqual(options['initial_prompt'], 'Earlier.')
        self.assertEqual(options['beam_size'], 1)
        self.assertFalse(options['without_timestamps'])
        self.assertEqual(result, {'text': 'Hallo zusammen. Los geht es.', 'language': 'de',
                                  'language_probability': 0.9, 'duration': 2.0})

    @skipUnless(HAS_NUMPY, NO_NUMPY)
    def test_unsure_language_assumes_main_language(self):
        model = FakeWhisperModel([_segment('Hello')], detected=('nl', 0.4))
        result = self._transcribe(model, main_language='en-GB')
        self.assertEqual(model.calls[0][1]['language'], 'en')
        self.assertEqual(result['language_probability'], 0.0, "assumed, not detected")

    @skipUnless(HAS_NUMPY, NO_NUMPY)
    def test_unsure_language_without_main_language(self):
        model = FakeWhisperModel([_segment('Hallo')], detected=('nl', 0.4))
        result = self._transcribe(model)
        self.assertEqual(model.calls[0][1]['language'], 'nl')
        self.assertEqual(result['language_probability'], 0.4)

    @skipUnless(HAS_NUMPY, NO_NUMPY)
    def test_given_language(self):
        model = FakeWhisperModel([_segment('Hello')])
        self._transcribe(model, language='en-US', workers=2)
        self.assertEqual(model.detect_calls, 0)
        self.assertEqual(model.calls[0][1]['language'], 'en')
        self.assertNotIn('hotwords', model.calls[0][1])
        self.assertNotIn('initial_prompt', model.calls[0][1])
        model = FakeWhisperModel([_segment('Hello')], detected=('en', 0.95))
        self._transcribe(model, language='ja')
        self.assertEqual(model.calls[0][1]['language'], 'en', "an unsupported language is detected instead")

    def test_compressed_audio_goes_through_a_file(self):
        model = FakeWhisperModel([_segment('Hello')], probability=0.7)
        result = self._transcribe(model, audio=b'\x1aE\xdf\xa3webm')
        path, options, existed = model.calls[0]
        self.assertTrue(path.endswith('.webm'))
        self.assertTrue(existed)
        self.assertFalse(os.path.exists(path), "the temporary file is removed")
        self.assertEqual(model.detect_calls, 0)
        self.assertIsNone(options['language'], "left to the model to detect")
        self.assertEqual(result['language_probability'], 0.7)

    @skipUnless(HAS_NUMPY, NO_NUMPY)
    def test_known_phrase_kept_only_when_confident(self):
        model = FakeWhisperModel([_segment('Thank you.', logprob=-0.8)])
        self.assertEqual(self._transcribe(model, language='en')['text'], '')
        model = FakeWhisperModel([_segment('Thank you.', logprob=-0.2, no_speech=0.05)])
        self.assertEqual(self._transcribe(model, language='en')['text'], 'Thank you.')
        model = FakeWhisperModel([])
        self.assertEqual(self._transcribe(model, language='en')['text'], '')

    def _fake_faster_whisper(self):
        av = types.ModuleType('av')
        av.open = MagicMock()
        audio = types.ModuleType('faster_whisper.audio')
        audio.av = av
        faster_whisper = types.ModuleType('faster_whisper')
        faster_whisper.audio = audio
        faster_whisper.WhisperModel = MagicMock(side_effect=lambda *args, **kwargs: object())
        self.startPatcher(patch.dict(sys.modules, {'faster_whisper': faster_whisper,
                                                   'faster_whisper.audio': audio}))
        return faster_whisper, av

    def test_patch_faster_whisper_av(self):
        _faster_whisper, av = self._fake_faster_whisper()
        orig_open = av.open
        stt_worker.patch_faster_whisper_av()
        av.open('meeting.webm', metadata_errors='ignore', mode='r')
        orig_open.assert_called_once_with('meeting.webm', mode='r')

    def test_whisper_model_loaded_once(self):
        faster_whisper, _av = self._fake_faster_whisper()
        self.startPatcher(patch.dict(stt_worker._whisper_models, clear=True))
        model = stt_worker.whisper_model('small')
        self.assertIs(stt_worker.whisper_model('small'), model)
        faster_whisper.WhisperModel.assert_called_once()
        self.assertEqual(faster_whisper.WhisperModel.call_args.kwargs['num_workers'], 1)
        self.assertIsNot(stt_worker.whisper_model('small', workers=2), model, "loaded again for 2 workers")
        self.assertEqual(faster_whisper.WhisperModel.call_args.kwargs['num_workers'], 2)
        with patch.object(stt_worker, '_whistle_loaded', False):
            self.assertEqual(stt_worker.loaded_models(), [['whisper', 'small', 2]])


@tagged('post_install', '-at_install')
class TestSpeechWorkerWhistle(TransactionCase):
    """Whistle transcription with a fake ``needle`` library, and routing requests to an engine."""

    def setUp(self):
        super().setUp()
        self.needle = types.ModuleType('needle')
        self.needle.transcribe = MagicMock(return_value={'text': '[Music] Guten Morgen', 'language': 'de'})
        self.startPatcher(patch.dict(sys.modules, {'needle': self.needle}))
        self.startPatcher(patch.dict(os.environ))
        self.startPatcher(patch.object(stt_worker, '_whistle_loaded', False))

    @skipUnless(HAS_NUMPY, NO_NUMPY)
    def test_transcribe_whistle(self):
        self.assertEqual(stt_worker.loaded_models(), [])
        result = stt_worker.transcribe_whistle(stt_client._silent_wav(), 'de-DE', ['Odoo'])
        self.assertEqual(result, {'text': 'Guten Morgen', 'language': 'de', 'language_probability': 0.0})
        self.assertEqual(self.needle.transcribe.call_args.kwargs, {'language': 'de', 'keywords': ['Odoo']})
        self.assertEqual(os.environ['NEEDLE_TELEMETRY'], '0')
        self.assertIn(['whistle', None], stt_worker.loaded_models())

    def test_whistle_skips_what_it_cannot_handle(self):
        self.assertEqual(stt_worker.transcribe_whistle(stt_client._silent_wav(), 'ja', []), {'text': ''})
        self.assertEqual(stt_worker.transcribe_whistle(b'OggS', 'auto', []), {'text': ''}, "WAV only")
        self.needle.transcribe.assert_not_called()

    def test_handle(self):
        with patch.object(stt_worker, 'transcribe_whistle', return_value={'text': 'a'}) as whistle:
            self.assertEqual(stt_worker.handle({'engine': 'whistle', 'language': 'en'}, b'audio'), {'text': 'a'})
        whistle.assert_called_once_with(b'audio', 'en', [])
        with patch.object(stt_worker, 'transcribe_whisper', return_value={'text': 'b'}) as whisper:
            stt_worker.handle({'engine': 'whisper', 'language': 'auto', 'model': None, 'keywords': ['Odoo'],
                               'prompt': 'Earlier.', 'beam_size': '1', 'main_language': 'en', 'workers': 2},
                              b'audio')
        whisper.assert_called_once_with(
            b'audio', 'auto', 'small', ['Odoo'], prompt='Earlier.', beam_size=1, main_language='en',
            without_timestamps=True, workers=2)
        with self.assertRaisesRegex(ValueError, 'unknown engine'):
            stt_worker.handle({'engine': 'nope'}, b'audio')


@tagged('post_install', '-at_install')
class TestSpeechWorkerConnection(TransactionCase):
    """One connection to the worker, over a socket pair."""

    def _serve(self, send=None, handle=None, scheduler=None):
        conn, client = socket.socketpair()
        self.addCleanup(client.close)
        with patch.object(stt_worker, 'handle', **(handle or {'return_value': {'text': 'Hello'}})):
            thread = threading.Thread(target=stt_worker.serve_connection,
                                      args=(conn, scheduler or stt_worker.Scheduler()))
            thread.start()
            stream = client.makefile('rwb')
            hello = json.loads(stream.readline())
            if send is not None:
                stream.write(send)
                stream.flush()
            client.shutdown(socket.SHUT_WR)
            reply = stream.readline()
            thread.join(10)
        self.assertFalse(thread.is_alive())
        return hello, json.loads(reply) if reply else None

    def _request(self, audio=b'audio', **header):
        return json.dumps(dict({'engine': 'whisper', 'size': len(audio)}, **header)).encode() + b'\n' + audio

    def test_hello_only(self):
        hello, reply = self._serve()
        self.assertEqual(hello['pid'], os.getpid())
        self.assertIn('loaded', hello)
        self.assertIsNone(reply)

    def test_bad_request_is_dropped(self):
        self.assertIsNone(self._serve(b'not json\n')[1])
        self.assertIsNone(self._serve(self._request()[:-2])[1], "audio cut short")

    def test_reply(self):
        _hello, reply = self._serve(self._request())
        self.assertEqual(reply['text'], 'Hello')
        self.assertIn('queue_seconds', reply)
        self.assertIn('stt_seconds', reply)

    def test_errors_keep_the_worker_serving(self):
        scheduler = stt_worker.Scheduler()
        reply = self._serve(self._request(), {'side_effect': RuntimeError('boom')}, scheduler)[1]
        self.assertEqual(reply['error'], "RuntimeError('boom')")
        reply = self._serve(self._request(), {'side_effect': ImportError('no needle')}, scheduler)[1]
        self.assertEqual(reply['error'], 'not_installed: no needle')
        self.assertTrue(scheduler.acquire(0), "the turn was given back")

    def test_busy(self):
        scheduler = stt_worker.Scheduler()
        scheduler.acquire(0)
        _hello, reply = self._serve(self._request(lock_timeout=0), scheduler=scheduler)
        self.assertEqual(reply, {'error': 'busy'})

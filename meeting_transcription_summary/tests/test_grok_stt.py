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
from unittest.mock import MagicMock, patch

import requests

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.meeting_transcription_summary.tools import grok_stt


def _reply(status=200, json_data=None):
    response = MagicMock(status_code=status, text='raw reply')
    response.json.return_value = json_data
    return response


@tagged('post_install', '-at_install')
class TestGrokStt(TransactionCase):
    """The Grok STT client: the request sent, and why a failed one failed."""

    def test_request(self):
        reply = _reply(json_data={'text': 'Hello Ash.', 'language': 'en'})
        with patch.object(grok_stt._session, 'post', return_value=reply) as post:
            result = grok_stt.transcribe(b'RIFF audio', 'xai-test', language='en-US', keywords=['Ash', ' Ash ', ''])
        self.assertEqual(result['text'], 'Hello Ash.')
        self.assertEqual(post.call_args.kwargs['headers'], {'Authorization': 'Bearer xai-test'})
        self.assertEqual(post.call_args.kwargs['data'], [
            ('model', grok_stt.MODEL), ('language', 'en'), ('format', 'true'), ('keyterm', 'Ash')])

    def _error(self, **post):
        with patch.object(grok_stt._session, 'post', **post), \
                self.assertRaises(grok_stt.GrokSttError) as caught:
            grok_stt.transcribe(b'RIFF audio', 'xai-test')
        return caught.exception

    def test_errors(self):
        error = self._error(return_value=_reply(401, {'error': {'message': 'Invalid API key'}}))
        self.assertIn('returned 401: Invalid API key', str(error))
        self.assertEqual((error.kind, error.status), ('auth', 401))
        error = self._error(return_value=_reply(429, {'error': 'Too many requests'}))
        self.assertIn('Too many requests', str(error))
        self.assertEqual((error.kind, error.status), ('rate_limit', 429))
        error = self._error(return_value=_reply(500, None))
        self.assertIn('returned 500: raw reply', str(error))
        self.assertEqual((error.kind, error.status), ('error', 500))
        self.assertEqual(self._error(side_effect=requests.ConnectionError('refused')).kind, 'unreachable')
        self.assertEqual(self._error(side_effect=requests.ReadTimeout('slow')).kind, 'timeout')
        unreadable = _reply()
        unreadable.json.side_effect = ValueError('not JSON')
        self.assertEqual(self._error(return_value=unreadable).kind, 'error')
        with patch.object(grok_stt, 'MAX_FILE_BYTES', 4), \
                self.assertRaisesRegex(grok_stt.GrokSttError, '500 MB') as caught:
            grok_stt.transcribe(b'RIFF audio', 'xai-test')
        self.assertEqual(caught.exception.kind, 'too_large')

    def test_request_options(self):
        keywords = ['K%03d' % i for i in range(120)] + ['x' * 80]
        with patch.object(grok_stt._session, 'post', return_value=_reply(json_data={'text': ''})) as post:
            grok_stt.transcribe(b'audio', 'xai-test', filename='meeting.mp3', language='nl-BE',
                                keywords=keywords, diarize=True, timeout=(10, 3600))
        kwargs = post.call_args.kwargs
        data = kwargs['data']
        self.assertIn(('language', 'nl'), data)
        self.assertNotIn(('format', 'true'), data, "no written-form formatting for Dutch")
        self.assertIn(('diarize', 'true'), data)
        terms = [value for name, value in data if name == 'keyterm']
        self.assertEqual(len(terms), grok_stt.MAX_KEYTERMS)
        self.assertEqual(terms[0], 'K000')
        self.assertEqual(kwargs['files'], {'file': ('meeting.mp3', b'audio')})
        self.assertEqual(kwargs['timeout'], (10, 3600))
        self.assertEqual(post.call_args.args[0], grok_stt.ENDPOINT)

        with patch.object(grok_stt._session, 'post', return_value=_reply(json_data={'text': ''})) as post:
            grok_stt.transcribe(b'audio', 'xai-test', keywords=['x' * 80])
        self.assertEqual(post.call_args.kwargs['data'], [('model', grok_stt.MODEL), ('keyterm', 'x' * 50)],
                         "auto-detected language, keyterm cut to the API's limit")

    def test_grok_language(self):
        self.assertIsNone(grok_stt.grok_language(None))
        self.assertIsNone(grok_stt.grok_language('auto'))
        self.assertEqual(grok_stt.grok_language('en-US'), 'en')
        self.assertEqual(grok_stt.grok_language('PT-br'), 'pt')
        self.assertEqual(grok_stt.grok_language('es-ES'), 'es-ES', "a regional variant it lists")
        self.assertEqual(grok_stt.grok_language('ar-SA'), 'ar-SA')
        self.assertIsNone(grok_stt.grok_language('xx'), "unsupported: auto-detected instead")

    def test_error_details(self):
        not_json = _reply(502)
        not_json.json.side_effect = ValueError('not JSON')
        error = self._error(return_value=not_json)
        self.assertIn('returned 502: raw reply', str(error))
        self.assertEqual((error.kind, error.status), ('error', 502))
        error = self._error(return_value=_reply(403, {'error': {'code': 7}}))
        self.assertIn("{'code': 7}", str(error))
        self.assertEqual(error.kind, 'auth')
        error = self._error(return_value=_reply(400, {'error': 'x' * 500}))
        self.assertLess(len(str(error)), 350, "a long detail is cut")


@tagged('post_install', '-at_install')
class TestGrokSpeakerTranscript(TransactionCase):
    """Turning a diarized Grok reply into one line per speaker turn."""

    def test_without_speakers(self):
        self.assertEqual(grok_stt.speaker_transcript({'text': ' Hello. '}), 'Hello.')
        self.assertEqual(grok_stt.speaker_transcript({'text': None, 'words': None}), '')
        words = [{'text': 'Hello', 'start': 0, 'speaker': 0}, {'text': 'there', 'start': 1, 'speaker': 0}]
        self.assertEqual(grok_stt.speaker_transcript({'text': 'Hello there', 'words': words}), 'Hello there',
                         "a single voice")

    def test_speaker_turns(self):
        words = [
            {'text': 'Hello', 'start': 0.4, 'speaker': 0},
            {'text': ',', 'start': 0.8, 'speaker': 0},
            {'text': 'Anna', 'start': 0.9, 'speaker': 0},
            {'text': ' ', 'start': 1.0, 'speaker': 1},
            {'text': '.', 'start': 1.1, 'speaker': 0},
            {'text': 'Hi', 'start': 3725.2, 'speaker': 1},
            {'text': '!', 'start': 3725.5, 'speaker': 1},
            {'text': 'Who', 'start': 3730, 'speaker': None},
            {'text': 'Done', 'start': None, 'speaker': 0},
        ]
        self.assertEqual(grok_stt.speaker_transcript({'text': 'ignored', 'words': words}), '\n'.join([
            '[00:00:00] Speaker 1: Hello, Anna.',
            '[01:02:05] Speaker 2: Hi!',
            '[01:02:10] Speaker: Who',
            '[00:00:00] Speaker 1: Done',
        ]))

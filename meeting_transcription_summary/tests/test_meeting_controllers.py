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
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import requests

from odoo import http
from odoo.exceptions import UserError
from odoo.tests import HttpCase, new_test_user, tagged

from odoo.addons.meeting_transcription_summary.controllers import main
from odoo.addons.meeting_transcription_summary.tools import cloud_whisper, grok_stt, stt_client

CONTROLLER_LOGGER = 'odoo.addons.meeting_transcription_summary.controllers.main'

WAV = b'RIFF' + b'\0' * 4000  # long enough to be transcribed; the engine is mocked


@tagged('post_install', '-at_install')
class TestMeetingRoutes(HttpCase):
    """The routes the browser calls during a meeting, as an internal user and as a guest."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alice = new_test_user(cls.env, login='route_alice', name='Alice Martin', groups='base.group_user')
        cls.channel = cls.env['discuss.channel'].create({'name': 'Ops Review', 'channel_type': 'group'})
        cls.alice_member = cls.channel.channel_member_ids.filtered(lambda m: m.partner_id == cls.alice.partner_id) \
            or cls.env['discuss.channel.member'].create({'channel_id': cls.channel.id,
                                                         'partner_id': cls.alice.partner_id.id})
        cls.guest = cls.env['mail.guest'].create({'name': 'Visitor'})
        cls.guest_member = cls.env['discuss.channel.member'].create({'channel_id': cls.channel.id,
                                                                     'guest_id': cls.guest.id})
        # joined one at a time, as in a real call: the first session opens the call
        for member in (cls.alice_member, cls.guest_member):
            cls.env['discuss.channel.rtc.session'].create({'channel_member_id': member.id})
        cls.env['ir.config_parameter'].sudo().set_param('meeting_transcription_summary.stt_engine', 'whisper')
        cls.meeting = cls.env['discuss.meeting.summary']._get_live_meeting(cls.channel)

    def setUp(self):
        super().setUp()
        # no speech worker in tests: loading a model in the background is skipped
        patcher = patch.object(stt_client, 'warm_up')
        self.warm_up = patcher.start()
        self.addCleanup(patcher.stop)

    def url_open(self, *args, **kwargs):
        # the server sees what the test wrote, and the test then reads what the server wrote
        self.env.flush_all()
        response = super().url_open(*args, **kwargs)
        self.env.invalidate_all()
        return response

    def _as_guest(self):
        self.authenticate(None, None)
        self.opener.cookies.set('dgid', self.guest._format_auth_cookie())

    def _caption(self, text='We will send the report on Friday.', **data):
        reply = {'text': text, 'language': 'en', 'language_probability': 1.0,
                 'queue_seconds': 0.0, 'stt_seconds': 0.1}
        with patch.object(stt_client, 'transcribe_with_info', return_value=reply) as transcribe:
            response = self.url_open('/discuss/meeting/transcribe_chunk', data={
                'channel_id': self.channel.id, 'csrf_token': http.Request.csrf_token(self), **data,
            }, files={'file': ('audio.wav', WAV, 'audio/wav')})
        return response.json(), transcribe

    def test_only_internal_users_switch_transcription(self):
        self._as_guest()
        result = self.make_jsonrpc_request('/discuss/meeting/set_transcribe',
                                           {'channel_id': self.channel.id, 'enabled': True})
        self.assertEqual(result, {'error': 'not_allowed'})
        self.assertFalse(self.meeting.transcribe_enabled)

        self.authenticate('route_alice', 'route_alice')
        result = self.make_jsonrpc_request('/discuss/meeting/set_transcribe',
                                           {'channel_id': self.channel.id, 'enabled': True})
        self.assertEqual(result, {'channel_id': self.channel.id, 'transcribe': True, 'subtitles': False})
        self.assertTrue(self.meeting.transcribe_enabled)
        self.warm_up.assert_called_once()

        self._as_guest()
        state = self.make_jsonrpc_request('/discuss/meeting/state', {'channel_id': self.channel.id})
        self.assertTrue(state['transcribe'], "guests still see that the call is transcribed")

        self.authenticate('route_alice', 'route_alice')
        result = self.make_jsonrpc_request('/discuss/meeting/set_transcribe',
                                           {'channel_id': self.channel.id, 'enabled': False})
        self.assertFalse(result['transcribe'])
        self.assertFalse(self.meeting.transcribe_enabled)

    def test_subtitles_alone_record_nothing(self):
        self.authenticate('route_alice', 'route_alice')
        self.make_jsonrpc_request('/discuss/meeting/set_subtitles', {'channel_id': self.channel.id, 'enabled': True})
        result, _transcribe = self._caption()
        self.assertEqual(result['text'], 'We will send the report on Friday.', "still captioned")
        self.assertFalse(self.meeting.transcript_line_ids)

    def test_transcribing_without_subtitles_broadcasts_no_caption(self):
        self.authenticate('route_alice', 'route_alice')
        self.make_jsonrpc_request('/discuss/meeting/set_transcribe', {'channel_id': self.channel.id, 'enabled': True})
        with patch.object(type(self.env['discuss.channel']), '_broadcast_meeting_subtitle') as broadcast:
            result, _transcribe = self._caption()
        self.assertEqual(result['status'], 'ok')
        broadcast.assert_not_called()
        self.assertEqual(self.meeting.transcript_line_ids.text, 'We will send the report on Friday.')

    def test_generate_summary_link(self):
        meeting = self.env['discuss.meeting.summary'].create({
            'name': 'Finished call', 'channel_id': self.channel.id, 'state': 'draft',
            'raw_transcript': 'Alice Martin: We agreed on March.',
        })
        self.authenticate('route_alice', 'route_alice')
        page = self.url_open(f'/discuss/meeting/generate_summary_redirect?summary_id={meeting.id}')
        self.assertIn('csrf_token', page.text, "the link only asks for confirmation")
        self.assertEqual(meeting.state, 'draft')
        self.url_open('/discuss/meeting/generate_summary_redirect', data={
            'summary_id': meeting.id, 'csrf_token': http.Request.csrf_token(self),
        }, allow_redirects=False)
        self.assertEqual(meeting.state, 'posted')
        self.assertIn('We agreed on March.', meeting.decisions)

    def test_generate_summary_link_redirects(self):
        self.authenticate('route_alice', 'route_alice')
        for summary_id in ('abc', 9999999):
            response = self.url_open(f'/discuss/meeting/generate_summary_redirect?summary_id={summary_id}',
                                     allow_redirects=False)
            self.assertTrue(response.headers['Location'].endswith('/odoo/discuss'), summary_id)
        meeting = self.env['discuss.meeting.summary'].create({
            'name': 'Posted call', 'channel_id': self.channel.id, 'state': 'posted'})
        response = self.url_open(f'/discuss/meeting/generate_summary_redirect?summary_id={meeting.id}',
                                 allow_redirects=False)
        self.assertTrue(response.headers['Location'].endswith(f'/odoo/discuss?channel_id={self.channel.id}'),
                        "a posted summary is not generated again")

    def test_not_in_call(self):
        other = self.env['discuss.channel'].create({'name': 'Elsewhere', 'channel_type': 'group'})
        self.authenticate('route_alice', 'route_alice')
        for route in ('/discuss/meeting/state', '/discuss/meeting/transcript'):
            self.assertEqual(self.make_jsonrpc_request(route, {'channel_id': other.id}), {'error': 'not_in_call'})

    def test_caption_idle_without_subtitles_or_transcription(self):
        self.authenticate('route_alice', 'route_alice')
        result, transcribe = self._caption()
        self.assertEqual(result['status'], 'idle')
        transcribe.assert_not_called()

    def test_caption_recorded_while_transcribing(self):
        self.authenticate('route_alice', 'route_alice')
        self.make_jsonrpc_request('/discuss/meeting/set_transcribe', {'channel_id': self.channel.id, 'enabled': True})
        result, transcribe = self._caption()
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['text'], 'We will send the report on Friday.')
        self.assertEqual(transcribe.call_args.args[1], 'whisper')
        self.assertEqual(self.meeting.transcript_line_ids.text, 'We will send the report on Friday.')
        self.assertEqual(self.meeting.transcript_line_ids.speaker_name, 'Alice Martin')

        transcript = self.make_jsonrpc_request('/discuss/meeting/transcript', {'channel_id': self.channel.id})
        self.assertTrue(transcript['transcribe'])
        self.assertEqual([line['text'] for line in transcript['lines']], ['We will send the report on Friday.'])

        summary = self.make_jsonrpc_request('/discuss/meeting/summarize', {'channel_id': self.channel.id})
        self.assertEqual(summary['status'], 'success')
        self.assertIn('Will send the report on Friday.', summary['action_items'])

        posted = self.make_jsonrpc_request('/discuss/meeting/post_summary', {'summary_id': summary['summary_id']})
        self.assertEqual(posted, {'status': 'posted'})
        again = self.make_jsonrpc_request('/discuss/meeting/post_summary', {'summary_id': summary['summary_id']})
        self.assertIn('error', again)

    def test_guest_captions_while_subtitles_are_on(self):
        self._as_guest()
        state = self.make_jsonrpc_request('/discuss/meeting/set_subtitles',
                                          {'channel_id': self.channel.id, 'enabled': True})
        self.assertTrue(state['subtitles'])
        result, _transcribe = self._caption('Hello everyone.')
        self.assertEqual((result['status'], result['text']), ('ok', 'Hello everyone.'))
        self.assertFalse(self.meeting.transcript_line_ids, "subtitles alone record nothing")
        self.meeting.transcribe_enabled = True  # turned on by an internal user
        self._caption('Thanks for joining.')
        self.assertEqual(self.meeting.transcript_line_ids.text, 'Thanks for joining.',
                         "a guest's speech is recorded while the call is transcribed")

    def test_caption_uses_speech_workers_setting(self):
        self.authenticate('route_alice', 'route_alice')
        self.make_jsonrpc_request('/discuss/meeting/set_subtitles', {'channel_id': self.channel.id, 'enabled': True})
        set_param = self.env['ir.config_parameter'].sudo().set_param
        # one by default; anything invalid falls back to one, too many is capped
        for value, workers in ((False, 1), ('2', 2), ('9', 4), ('0', 1), ('many', 1)):
            set_param('meeting_transcription_summary.stt_workers', value)
            _result, transcribe = self._caption()
            self.assertEqual(transcribe.call_args.kwargs['workers'], workers, value)

    def test_short_chunk(self):
        self.authenticate('route_alice', 'route_alice')
        self.make_jsonrpc_request('/discuss/meeting/set_subtitles', {'channel_id': self.channel.id, 'enabled': True})
        with patch.object(stt_client, 'transcribe_with_info') as transcribe:
            response = self.url_open('/discuss/meeting/transcribe_chunk', data={
                'channel_id': self.channel.id, 'csrf_token': http.Request.csrf_token(self),
            }, files={'file': ('audio.wav', b'RIFF', 'audio/wav')})
        self.assertEqual(response.json(), {'status': 'empty_chunk'})
        transcribe.assert_not_called()

    def test_caption_with_cloud_whisper(self):
        self.authenticate('route_alice', 'route_alice')
        self.make_jsonrpc_request('/discuss/meeting/set_subtitles', {'channel_id': self.channel.id, 'enabled': True})
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('meeting_transcription_summary.stt_engine', 'cloud_whisper')
        set_param('meeting_transcription_summary.cloud_whisper_url', 'https://api.openai.com/v1')
        set_param('meeting_transcription_summary.cloud_whisper_model', 'whisper-1')
        set_param('meeting_transcription_summary.cloud_whisper_api_key', 'sk-test')
        cloud = patch.object(cloud_whisper, 'transcribe', return_value={'text': 'Ship it today.', 'language': 'en'})
        with cloud as transcribe:
            result, local = self._caption()
        self.assertEqual((result['status'], result['text']), ('ok', 'Ship it today.'))
        self.assertNotIn('caption_error', result)
        local.assert_not_called()
        self.assertEqual(transcribe.call_args.args[1], 'sk-test')
        self.assertEqual((transcribe.call_args.kwargs['url'], transcribe.call_args.kwargs['model']),
                         ('https://api.openai.com/v1', 'whisper-1'))
        self.assertIn('Alice Martin', transcribe.call_args.kwargs['keywords'])

        # a lost caption tells the speaker why
        for error, reason in (
            (cloud_whisper.CloudWhisperError('429', 'rate_limit', 429), "reached this account's request limit"),
            (cloud_whisper.CloudWhisperError('401', 'auth', 401), 'rejected the API key'),
            (cloud_whisper.CloudWhisperError('slow', 'timeout'), 'did not answer within 15 seconds'),
            (cloud_whisper.CloudWhisperError('down', 'unreachable'), 'could not be reached'),
            (cloud_whisper.CloudWhisperError('502', 'error', 502), 'returned an error (HTTP 502)'),
        ):
            with patch.object(cloud_whisper, 'transcribe', side_effect=error):
                result, _local = self._caption()
            self.assertEqual((result['status'], result['text']), ('ok', ''), "a failed caption is skipped")
            self.assertIn('api.openai.com', result['caption_error'])
            self.assertIn(reason, result['caption_error'])

    def test_caption_with_grok_errors(self):
        self.authenticate('route_alice', 'route_alice')
        self.make_jsonrpc_request('/discuss/meeting/set_subtitles', {'channel_id': self.channel.id, 'enabled': True})
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('meeting_transcription_summary.stt_engine', 'grok')
        set_param('meeting_transcription_summary.stt_openai_fallback', False)
        set_param('meeting_transcription_summary.xai_api_key', '')
        with patch.object(grok_stt, 'transcribe') as transcribe:
            result, _local = self._caption()
        transcribe.assert_not_called()
        self.assertIn('no xAI API key is set', result['caption_error'])

        set_param('meeting_transcription_summary.xai_api_key', 'xai-test')
        with patch.object(grok_stt, 'transcribe', return_value={'text': 'Ship it today.', 'language': 'en'}):
            result, local = self._caption()
        self.assertEqual(result['text'], 'Ship it today.')
        self.assertNotIn('caption_error', result)
        local.assert_not_called()
        for error, reason in (
            (grok_stt.GrokSttError('429', 'rate_limit', 429), "reached this account's request limit"),
            (grok_stt.GrokSttError('401', 'auth', 401), 'rejected the API key'),
            (grok_stt.GrokSttError('slow', 'timeout'), 'did not answer within 15 seconds'),
            (grok_stt.GrokSttError('down', 'unreachable'), 'could not be reached'),
            (grok_stt.GrokSttError('500', 'error', 500), 'returned an error (HTTP 500)'),
            (grok_stt.GrokSttError('unreadable'), 'could not transcribe it'),
        ):
            with patch.object(grok_stt, 'transcribe', side_effect=error):
                result, _local = self._caption()
            self.assertEqual((result['status'], result['text']), ('ok', ''), "a failed caption is skipped")
            self.assertIn('xAI', result['caption_error'])
            self.assertIn(reason, result['caption_error'])

    def test_caption_engine_not_installed(self):
        self.authenticate('route_alice', 'route_alice')
        self.make_jsonrpc_request('/discuss/meeting/set_subtitles', {'channel_id': self.channel.id, 'enabled': True})
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('meeting_transcription_summary.stt_engine', 'whistle')
        set_param('meeting_transcription_summary.stt_openai_fallback', False)

        def transcribe(_audio, engine, *args, **kwargs):
            raise stt_client.SttWorkerUnavailable("not_installed: No module named %s" % engine)

        def caption():
            with patch.object(stt_client, 'transcribe_with_info', side_effect=transcribe):
                return self.url_open('/discuss/meeting/transcribe_chunk', data={
                    'channel_id': self.channel.id, 'csrf_token': http.Request.csrf_token(self),
                }, files={'file': ('audio.wav', WAV, 'audio/wav')}).json()

        # the speaker is told what to install
        result = caption()
        self.assertEqual(result['text'], '')
        self.assertIn('Whistle speech engine is not installed', result['caption_error'])
        self.assertIn('pip install cactus-needle', result['caption_error'])

    def test_summarize_without_transcript(self):
        self.authenticate('route_alice', 'route_alice')
        result = self.make_jsonrpc_request('/discuss/meeting/summarize', {'channel_id': self.channel.id})
        self.assertIn('Nothing has been transcribed', result['error'])

    def test_upload_recording(self):
        self.authenticate('route_alice', 'route_alice')
        response = self.url_open('/discuss/meeting/upload_recording', data={
            'channel_id': self.channel.id, 'title': 'Board meeting', 'csrf_token': http.Request.csrf_token(self),
        }, files={'file': ('board.mp3', b'ID3 fake audio', 'audio/mpeg')})
        result = response.json()
        self.assertEqual(result['status'], 'success')
        meeting = self.env['discuss.meeting.summary'].browse(result['summary_id'])
        self.assertEqual((meeting.name, meeting.state), ('Board meeting', 'processing'))
        self.assertTrue(meeting.post_when_done)
        self.assertEqual(meeting.requested_by_id, self.alice)

        response = self.url_open('/discuss/meeting/upload_recording', data={
            'channel_id': self.channel.id, 'csrf_token': http.Request.csrf_token(self),
        })
        self.assertEqual(response.json()['status'], 'error')

    # Rejected requests

    def _post_chunk(self, data=None, files=None, **transcribe):
        with patch.object(stt_client, 'transcribe_with_info', **transcribe) as local:
            response = self.url_open('/discuss/meeting/transcribe_chunk', data={
                'csrf_token': http.Request.csrf_token(self), **(data or {}),
            }, files=files if files is not None else {'file': ('audio.wav', WAV, 'audio/wav')})
        return response, local

    def test_caption_rejected(self):
        self.authenticate('route_alice', 'route_alice')
        response, _local = self._post_chunk({'channel_id': self.channel.id}, files={})
        self.assertEqual(response.json(), {'error': 'Missing audio file or channel_id'})
        response, _local = self._post_chunk({})
        self.assertEqual(response.json(), {'error': 'Missing audio file or channel_id'})
        other = self.env['discuss.channel'].create({'name': 'Elsewhere', 'channel_type': 'group'})
        for channel_id in (other.id, 'not-a-number'):
            response, local = self._post_chunk({'channel_id': channel_id})
            self.assertEqual(response.status_code, 403, channel_id)
            self.assertEqual(response.json(), {'error': 'Channel not found'})
            local.assert_not_called()

    def test_routes_not_in_call(self):
        other = self.env['discuss.channel'].create({'name': 'Elsewhere', 'channel_type': 'group'})
        self.authenticate('route_alice', 'route_alice')
        result = self.make_jsonrpc_request('/discuss/meeting/set_subtitles', {'channel_id': other.id, 'enabled': True})
        self.assertEqual(result, {'error': 'not_in_call'})
        result = self.make_jsonrpc_request('/discuss/meeting/summarize', {'channel_id': other.id})
        self.assertEqual(result, {'error': 'Channel not found'})
        result = self.make_jsonrpc_request('/discuss/meeting/post_summary', {'summary_id': 999999999})
        self.assertEqual(result, {'error': 'Summary not found'})

    # Captions

    def test_caption_language_from_browser(self):
        self.authenticate('route_alice', 'route_alice')
        self.make_jsonrpc_request('/discuss/meeting/set_subtitles', {'channel_id': self.channel.id, 'enabled': True})
        self.env['ir.config_parameter'].sudo().set_param('meeting_transcription_summary.subtitles_language', 'auto')
        reply = {'text': 'Hallo.', 'language': 'de', 'language_probability': 0.9, 'queue_seconds': 0.0,
                 'stt_seconds': 0.1}
        # the language the browser already detected for this speaker, if it looks like one
        for sent, used in (('de', 'de'), ('Deutsch', 'auto'), ('', 'auto')):
            response, local = self._post_chunk({'channel_id': self.channel.id, 'language': sent}, return_value=reply)
            self.assertEqual(local.call_args.args[2], used, sent)
        result = response.json()
        self.assertEqual((result['language'], result['language_probability']), ('de', 0.9))

    def test_caption_keywords(self):
        self.authenticate('route_alice', 'route_alice')
        self.make_jsonrpc_request('/discuss/meeting/set_subtitles', {'channel_id': self.channel.id, 'enabled': True})
        self.env['ir.config_parameter'].sudo().set_param(
            'meeting_transcription_summary.keywords', 'Odoo, Ash\nAlice Martin,, ')
        _result, local = self._caption()
        self.assertEqual(local.call_args.args[4], ['Odoo', 'Ash', 'Alice Martin', 'Visitor'],
                         "configured terms, then the people in the call, each once")

    def test_caption_debug_audio(self):
        debug_dir = tempfile.mkdtemp(prefix='subtitle_debug')
        self.addCleanup(shutil.rmtree, debug_dir, True)
        self.authenticate('route_alice', 'route_alice')
        self.make_jsonrpc_request('/discuss/meeting/set_subtitles', {'channel_id': self.channel.id, 'enabled': True})
        self.env['ir.config_parameter'].sudo().set_param('meeting_transcription_summary.save_debug_audio', 'True')
        with patch.object(main, 'DEBUG_AUDIO_DIR', debug_dir):
            self._caption()
        saved = os.listdir(debug_dir)
        self.assertEqual(len(saved), 1)
        self.assertTrue(saved[0].endswith('_ch%d.wav' % self.channel.id))
        with open(os.path.join(debug_dir, saved[0]), 'rb') as f:
            self.assertEqual(f.read(), WAV)

    def test_save_debug_audio_keeps_the_last_ones(self):
        debug_dir = os.path.join(tempfile.mkdtemp(prefix='subtitle_debug'), 'clips')
        self.addCleanup(shutil.rmtree, os.path.dirname(debug_dir), True)
        with patch.object(main, 'DEBUG_AUDIO_DIR', debug_dir), patch.object(main, 'DEBUG_AUDIO_KEEP', 2), \
                patch.object(main.time, 'time', side_effect=[1.0, 2.0, 3.0]):
            paths = [main._save_debug_audio(b'clip %d' % i, 7) for i in range(3)]
        self.assertEqual(sorted(os.listdir(debug_dir)), ['2000_ch7.wav', '3000_ch7.wav'], "the oldest is removed")
        self.assertEqual(paths[-1], os.path.join(debug_dir, '3000_ch7.wav'))
        blocked = os.path.join(debug_dir, '3000_ch7.wav', 'sub')  # a file, not a directory
        with patch.object(main, 'DEBUG_AUDIO_DIR', blocked), self.assertLogs(CONTROLLER_LOGGER, 'ERROR'):
            self.assertIsNone(main._save_debug_audio(b'clip', 7), "a debug aid never fails the caption")

    def test_caption_local_engine_failed(self):
        self.authenticate('route_alice', 'route_alice')
        self.make_jsonrpc_request('/discuss/meeting/set_subtitles', {'channel_id': self.channel.id, 'enabled': True})
        with self.assertLogs(CONTROLLER_LOGGER, 'ERROR'):
            response, _local = self._post_chunk(
                {'channel_id': self.channel.id}, side_effect=stt_client.SttWorkerError('speech worker timed out'))
        result = response.json()
        self.assertEqual((result['status'], result['text']), ('ok', ''))
        self.assertNotIn('caption_error', result)
        response, _local = self._post_chunk(
            {'channel_id': self.channel.id}, side_effect=stt_client.SttWorkerUnavailable('speech worker busy'))
        self.assertEqual(response.json()['text'], '', "busy: this caption is skipped")

    def _openai_fallback(self, enabled=True):
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('meeting_transcription_summary.stt_openai_fallback', 'True' if enabled else False)
        set_param('meeting_transcription_summary.openai_api_key', 'sk-test')

    def _openai_reply(self, status=200, text='Saved by OpenAI.'):
        response = MagicMock(status_code=status, text='raw reply')
        response.json.return_value = {'text': ' %s ' % text}
        return response

    def test_openai_fallback(self):
        self.authenticate('route_alice', 'route_alice')
        self.make_jsonrpc_request('/discuss/meeting/set_subtitles', {'channel_id': self.channel.id, 'enabled': True})
        self._openai_fallback()
        busy = stt_client.SttWorkerUnavailable('speech worker busy')
        with patch.object(main.requests, 'post', return_value=self._openai_reply()) as post:
            response, _local = self._post_chunk({'channel_id': self.channel.id}, side_effect=busy)
        self.assertEqual(response.json()['text'], 'Saved by OpenAI.')
        self.assertEqual(post.call_args.args[0], 'https://api.openai.com/v1/audio/transcriptions')
        self.assertEqual(post.call_args.kwargs['headers'], {'Authorization': 'Bearer sk-test'})
        files = post.call_args.kwargs['files']
        self.assertEqual(files['file'][0], 'audio.wav')
        self.assertEqual(files['language'], (None, 'en'))

        self.env['ir.config_parameter'].sudo().set_param('meeting_transcription_summary.subtitles_language', 'auto')
        with patch.object(main.requests, 'post', return_value=self._openai_reply()) as post:
            self._post_chunk({'channel_id': self.channel.id}, side_effect=busy,
                             files={'file': ('audio.webm', b'\x1aE' + b'\0' * 2000, 'audio/webm')})
        files = post.call_args.kwargs['files']
        self.assertEqual(files['file'][0], 'audio.webm')
        self.assertNotIn('language', files, "left to OpenAI to detect")

    def test_openai_fallback_failures(self):
        self.authenticate('route_alice', 'route_alice')
        self.make_jsonrpc_request('/discuss/meeting/set_subtitles', {'channel_id': self.channel.id, 'enabled': True})
        self._openai_fallback()
        busy = stt_client.SttWorkerUnavailable('speech worker busy')
        for post in ({'return_value': self._openai_reply(500)}, {'side_effect': requests.ConnectionError('down')}):
            with patch.object(main.requests, 'post', **post), self.assertLogs(CONTROLLER_LOGGER, 'WARNING'):
                response, _local = self._post_chunk({'channel_id': self.channel.id}, side_effect=busy)
            self.assertEqual(response.json()['text'], '')

    def test_openai_fallback_only_when_needed(self):
        self.authenticate('route_alice', 'route_alice')
        self.make_jsonrpc_request('/discuss/meeting/set_subtitles', {'channel_id': self.channel.id, 'enabled': True})
        self._openai_fallback()
        silence = {'text': '', 'language': None, 'language_probability': 0.0, 'queue_seconds': 0.0,
                   'stt_seconds': 0.1}
        with patch.object(main.requests, 'post') as post:
            self._post_chunk({'channel_id': self.channel.id}, return_value=silence)
        post.assert_not_called()  # no words from the engine is silence, not a failure
        self._openai_fallback(enabled=False)
        with patch.object(main.requests, 'post') as post:
            self._post_chunk({'channel_id': self.channel.id},
                             side_effect=stt_client.SttWorkerUnavailable('speech worker busy'))
        post.assert_not_called()  # the key alone may be there for summaries only

    # Warming up the local engine

    def test_warm_up_when_captions_are_needed(self):
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('meeting_transcription_summary.whisper_model', 'medium')
        set_param('meeting_transcription_summary.stt_workers', '2')
        self.authenticate('route_alice', 'route_alice')
        self.make_jsonrpc_request('/discuss/meeting/state', {'channel_id': self.channel.id})
        self.warm_up.assert_not_called()  # nobody needs captions yet
        self.make_jsonrpc_request('/discuss/meeting/set_subtitles', {'channel_id': self.channel.id, 'enabled': True})
        self.warm_up.assert_called_once_with('whisper', 'medium', 2)
        self.warm_up.reset_mock()
        for engine in ('grok', 'cloud_whisper'):
            set_param('meeting_transcription_summary.stt_engine', engine)
            self.make_jsonrpc_request('/discuss/meeting/state', {'channel_id': self.channel.id})
        self.warm_up.assert_not_called()  # a cloud engine has no model to load
        set_param('meeting_transcription_summary.stt_engine', 'whistle')
        self.make_jsonrpc_request('/discuss/meeting/state', {'channel_id': self.channel.id})
        self.assertEqual(self.warm_up.call_args.args[0], 'whistle')

    # Recording upload

    def _upload(self, files=None, **data):
        return self.url_open('/discuss/meeting/upload_recording', data={
            'channel_id': self.channel.id, 'csrf_token': http.Request.csrf_token(self), **data,
        }, files=files if files is not None else {'file': ('board.mp3', b'ID3 fake audio', 'audio/mpeg')}).json()

    def test_upload_recording_rejected(self):
        self.authenticate('route_alice', 'route_alice')
        other = self.env['discuss.channel'].create({'name': 'Elsewhere', 'channel_type': 'group'})
        self.assertEqual(self._upload(channel_id=other.id), {'status': 'error', 'error': 'Channel not found'})
        self.assertEqual(self._upload(files={'file': ('empty.mp3', b'', 'audio/mpeg')}),
                         {'status': 'error', 'error': 'Uploaded file is empty'})
        result = self._upload(title='  ', duration_minutes='45')
        meeting = self.env['discuss.meeting.summary'].browse(result['summary_id'])
        self.assertEqual((meeting.name, meeting.duration_minutes), ('Recording: Ops Review', 45),
                         "a blank title is named after the channel")

    def test_upload_recording_failure_leaves_nothing(self):
        self.authenticate('route_alice', 'route_alice')
        Summary = self.env.registry['discuss.meeting.summary']
        count = self.env['discuss.meeting.summary'].search_count([])
        with patch.object(Summary, '_queue_recording_transcription', side_effect=UserError('Unsupported file.')):
            self.assertEqual(self._upload(), {'status': 'error', 'error': 'Unsupported file.'})
        with patch.object(Summary, '_queue_recording_transcription', side_effect=RuntimeError('disk full')), \
                self.assertLogs(CONTROLLER_LOGGER, 'ERROR'):
            result = self._upload()
        self.assertEqual(result['status'], 'error')
        self.assertNotIn('disk full', result['error'], "internal details stay in the log")
        self.assertEqual(self.env['discuss.meeting.summary'].search_count([]), count)

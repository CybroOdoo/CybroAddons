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
import base64
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import timedelta
from unittest.mock import MagicMock, patch

import requests

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase

from odoo.addons.meeting_transcription_summary.tools import stt_client

SUMMARY_MODULE = 'odoo.addons.meeting_transcription_summary.models.discuss_meeting_summary'
SETTINGS_MODULE = 'odoo.addons.meeting_transcription_summary.models.res_config_settings'


def json_response(payload, status_code=200):
    """A ``requests`` response answering ``payload`` as JSON."""
    response = MagicMock(status_code=status_code, text=json.dumps(payload))
    response.json.return_value = payload
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(f"{status_code} error")
    return response


class MeetingTestCommon(TransactionCase):
    """Two internal users in a group channel, with helpers to run a call."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.alice = new_test_user(cls.env, login='meeting_alice', name='Alice Martin', groups='base.group_user')
        cls.bob = new_test_user(cls.env, login='meeting_bob', name='Bob Stone', groups='base.group_user')
        cls.channel = cls.env['discuss.channel'].create({'name': 'Ops Review', 'channel_type': 'group'})
        cls.alice_member = cls._member(cls.channel, cls.alice.partner_id)
        cls.bob_member = cls._member(cls.channel, cls.bob.partner_id)
        cls.Summary = cls.env['discuss.meeting.summary']

    @classmethod
    def _member(cls, channel, partner):
        member = channel.channel_member_ids.filtered(lambda m: m.partner_id == partner)
        return member or cls.env['discuss.channel.member'].create({'channel_id': channel.id, 'partner_id': partner.id})

    def _start_call(self, *members):
        # one at a time, as people join: Odoo opens the call history with the first session
        RtcSession = self.env['discuss.channel.rtc.session']
        return RtcSession.concat(*(RtcSession.create({'channel_member_id': m.id}) for m in members))

    @contextmanager
    def _capture_bus(self):
        """The notification types the channel sends (Odoo sends them only once committed)."""
        sent = []
        Channel = type(self.channel)
        original = Channel._bus_send

        def spy(record, notification_type, message, **kwargs):
            sent.append(notification_type)
            return original(record, notification_type, message, **kwargs)

        with patch.object(Channel, '_bus_send', spy):
            yield sent

    def _last_message_body(self):
        return str(self.channel.message_ids.sorted('id')[-1:].body)

    def _meeting(self, **vals):
        return self.Summary.create({'name': 'Weekly review', 'channel_id': self.channel.id, **vals})


@tagged('post_install', '-at_install')
class TestMeetingCall(MeetingTestCommon):
    """A live call: its meeting, transcript, captions and end."""

    def test_call_start_creates_one_live_meeting(self):
        self._start_call(self.alice_member, self.bob_member)
        meeting = self.Summary._get_live_meeting(self.channel)
        self.assertEqual(meeting.state, 'live')
        self.assertEqual(meeting.name, 'Meeting: Ops Review')
        self.assertEqual(meeting.attendee_ids, self.alice.partner_id | self.bob.partner_id)
        self.assertTrue(meeting._is_call_running())
        # looked up again, never duplicated
        self.assertEqual(self.Summary._get_live_meeting(self.channel, create=True), meeting)

    def test_no_meeting_without_call(self):
        self.assertFalse(self.Summary._get_live_meeting(self.channel, create=True))
        self.assertFalse(self.channel._get_meeting_ai_state()['transcribe'])

    def test_transcript_only_while_transcribing(self):
        self.Summary._add_transcript_line(self.channel, self.alice_member, 'Alice Martin', 'Not recorded.')
        self.assertFalse(self.Summary.search([('channel_id', '=', self.channel.id)]).transcript_line_ids)
        sessions = self._start_call(self.alice_member)
        meeting = self.Summary._get_live_meeting(self.channel)
        sessions.meeting_subtitles_on = True
        self.Summary._add_transcript_line(self.channel, self.alice_member, 'Alice Martin', 'Not recorded.')
        self.assertFalse(meeting.transcript_line_ids, "subtitles alone record nothing")
        meeting.transcribe_enabled = True
        self.Summary._add_transcript_line(self.channel, self.alice_member, 'Alice Martin', '  We start now.  ')
        self.assertEqual(meeting.transcript_line_ids.text, 'We start now.')
        self.assertRegex(meeting._build_transcript(), r'^\[\d{2}:\d{2}:\d{2}\] Alice Martin: We start now\.$')

    def test_ai_state_and_broadcasts(self):
        sessions = self._start_call(self.alice_member, self.bob_member)
        state = self.channel._get_meeting_ai_state()
        self.assertEqual(state, {'channel_id': self.channel.id, 'transcribe': False, 'subtitles': False})
        sessions[0].meeting_subtitles_on = True
        self.assertEqual(self.channel._get_meeting_ai_state(),
                         {'channel_id': self.channel.id, 'transcribe': False, 'subtitles': True})
        self.Summary._get_live_meeting(self.channel).transcribe_enabled = True
        self.assertTrue(self.channel._get_meeting_ai_state()['transcribe'])

        with self._capture_bus() as sent:
            self.channel._broadcast_meeting_ai_state()
            self.assertTrue(self.channel._broadcast_meeting_subtitle('Alice Martin', 'Hello',
                                                                      partner_id=self.alice.partner_id.id,
                                                                      member_id=self.alice_member.id))
        self.assertEqual(sent, ['discuss.channel/meeting_ai_state', 'discuss.channel/meeting_subtitle'])

    def test_subtitle_viewer_leaving_updates_others(self):
        sessions = self._start_call(self.alice_member, self.bob_member)
        sessions[0].meeting_subtitles_on = True
        with self._capture_bus() as sent:
            sessions[0].unlink()
        self.assertIn('discuss.channel/meeting_ai_state', sent)
        self.assertFalse(self.channel._get_meeting_ai_state()['subtitles'])

    def test_call_without_transcript_leaves_nothing(self):
        sessions = self._start_call(self.alice_member)
        meeting = self.Summary._get_live_meeting(self.channel)
        sessions.unlink()
        self.assertFalse(meeting.exists())

    def test_call_end_keeps_transcript_and_invites_to_summarize(self):
        sessions = self._start_call(self.alice_member, self.bob_member)
        meeting = self.Summary._get_live_meeting(self.channel)
        meeting.transcribe_enabled = True
        self.Summary._add_transcript_line(self.channel, self.alice_member, 'Alice Martin', 'We will send the report.')
        self.Summary._add_transcript_line(self.channel, self.bob_member, 'Bob Stone', 'Agreed.')
        sessions.unlink()
        self.assertEqual(meeting.state, 'draft')
        self.assertFalse(meeting.transcribe_enabled, "switched off when the call ends")
        self.assertFalse(meeting.executive_summary, "the summary is generated on request, not when the call ends")
        self.assertEqual(len(meeting.raw_transcript.splitlines()), 2)
        self.assertGreaterEqual(meeting.duration_minutes, 1)
        prompt = self.channel.message_ids.sorted('id')[-1]
        self.assertEqual(prompt.author_id, self.env.ref('base.partner_root'))
        self.assertIn('Meeting Ended', str(prompt.body))
        self.assertIn(f'summary_id={meeting.id}', str(prompt.body))
        self.assertIn('Speech turns transcribed:', str(prompt.body))

    def test_summarize_again_after_posting_during_call(self):
        self._start_call(self.alice_member)
        meeting = self.Summary._get_live_meeting(self.channel)
        meeting.transcribe_enabled = True
        self.Summary._add_transcript_line(self.channel, self.alice_member, 'Alice Martin', 'We will send the report.')
        meeting.action_generate_summary()
        self.assertEqual(meeting.state, 'live')
        meeting.action_post_to_channel()
        self.assertEqual(meeting.state, 'posted')
        self.Summary._add_transcript_line(self.channel, self.alice_member, 'Alice Martin', 'We agreed on March.')
        meeting.action_generate_summary()
        self.assertIn('We agreed on March.', meeting.raw_transcript)
        self.assertIn('March', meeting.decisions)
        self.assertEqual(meeting.state, 'live', "a running call stays live until it ends")


@tagged('post_install', '-at_install')
class TestMeetingSummary(MeetingTestCommon):
    """Summaries: the built-in summarizer, the AI providers, posting."""

    def test_builtin_summarizer(self):
        transcript = (
            "[10:00:01] Alice: We will send the report on Friday.\n"
            "[10:00:05] Bob: We agreed to move the launch. The budget looks fine.\n"
            "[10:00:09] Bob: The budget looks fine!\n"
            "the office move is postponed"
        )
        result = self.Summary._builtin_summarize(transcript)
        self.assertEqual(result['action_items'], 'Alice: Will send the report on Friday.')
        self.assertEqual(result['decisions'], 'Bob: We agreed to move the launch.')
        self.assertEqual(result['key_discussion_points'].splitlines(),
                         ['Bob: The budget looks fine.', 'The office move is postponed.'])
        self.assertIn('<strong>', result['executive_summary'])
        self.assertIn('Alice', result['executive_summary'])

    def test_builtin_summarizer_one_line_recording(self):
        """A transcribed recording is one line of plain text: one entry per sentence."""
        result = self.Summary._builtin_summarize(
            "Good morning everyone. The budget for Q3 is approved. Priya will send the contract by Monday.")
        self.assertEqual(result['decisions'], 'The budget for Q3 is approved.')
        self.assertEqual(result['action_items'], 'Priya will send the contract by Monday.')
        self.assertEqual(result['key_discussion_points'], 'Good morning everyone.')

    def test_builtin_summarizer_edge_cases(self):
        only_tasks = self.Summary._builtin_summarize("Alice: I will send it")
        self.assertEqual(only_tasks['action_items'], 'Alice: Will send it.')
        self.assertEqual(only_tasks['key_discussion_points'], 'Alice: I will send it',
                         "with no plain discussion, the minutes still list what was said")
        empty = self.Summary._builtin_summarize("")
        self.assertIn('Participants', empty['executive_summary'])
        self.assertFalse(empty['key_discussion_points'])

    def test_builtin_action_items_spoken_forms(self):
        """Tasks as people say them in a call, with their owner."""
        action = self.Summary._builtin_action_item
        for sentence, expected in [
            ("I'll look into it.", "Priya: Will look into it."),
            ("I\u2019ll send the deck tonight.", "Priya: Will send the deck tonight."),
            ("We'll fix the login bug.", "Priya: Will fix the login bug."),
            ("I'm going to call the vendor.", "Priya: Will call the vendor."),
            ("Let me handle the invoices.", "Priya: Will handle the invoices."),
            ("We will send the report on Friday.", "Priya: Will send the report on Friday."),
            ("Rahul is going to update the sheet.", "Priya: Rahul is going to update the sheet."),
            ("They're gonna ship the fix.", "Priya: They're gonna ship the fix."),
            ("We need to update the docs.", "Priya: We need to update the docs."),
            ("The release is due by Friday.", "Priya: The release is due by Friday."),
            ("The next step is a demo for the client.", "Priya: The next step is a demo for the client."),
            ("Rahul is responsible for the rollout.", "Priya: Rahul is responsible for the rollout."),
            ("Please send me the invoice.", "Priya: Please send me the invoice."),
            ("Can you check the server, Arun?", "Arun: Can you check the server? (asked by Priya)"),
            ("Arun, could you update the sheet?", "Arun: Could you update the sheet? (asked by Priya)"),
        ]:
            self.assertEqual(action('Priya', sentence), expected, sentence)
        self.assertEqual(action('', "Can you check the server, Arun?"), "Arun: Can you check the server?",
                         "a recording without speakers has no one who asked")
        self.assertEqual(action('', "I'll send it."), "Will send it.")

    def test_builtin_not_action_items(self):
        """'Will' or 'must' about things, not people, and plain talk are no tasks."""
        for sentence in ("It will rain tomorrow.", "This must be the old version.", "Monday will be busy.",
                         "The budget will be fine.", "That will be all.", "I think so.", "Yes please.",
                         "Thank you everyone.", "What do you think?", "We agreed to move the launch.",
                         "Hello, can you hear me?", "Could you see my screen?", "Do you hear us now?"):
            self.assertIsNone(self.Summary._builtin_action_item('Priya', sentence), sentence)

    def test_builtin_request_without_named_owner(self):
        """A filler or a group before or after the comma is no owner: the task stays with the speaker."""
        action = self.Summary._builtin_action_item
        self.assertEqual(action('Priya', "Okay, can you check it?"), "Priya: Okay, can you check it?")
        self.assertEqual(action('Priya', "Could you all review it, Everyone?"),
                         "Priya: Could you all review it, Everyone?")
        self.assertEqual(action('Priya', "Can you share your screen?"), "Priya: Can you share your screen?")

    def test_builtin_summarizer_spoken_meeting(self):
        transcript = (
            "[10:00:01] Priya: Good morning everyone.\n"
            "[10:00:04] Priya: The new dashboard is live?\n"
            "[10:00:08] Arun: Yes, it went out yesterday. It will need some polish.\n"
            "[10:00:12] Priya: Arun, can you fix the chart colours?\n"
            "[10:00:15] Arun: Sure, I'll do it by Friday.\n"
            "[10:00:19] Rahul: We decided to keep the old export for now.\n"
            "[10:00:23] Rahul: Let me write the release notes."
        )
        result = self.Summary._builtin_summarize(transcript)
        self.assertEqual(result['action_items'].splitlines(), [
            'Arun: Can you fix the chart colours? (asked by Priya)',
            "Arun: Sure, I'll do it by Friday.",
            'Rahul: Will write the release notes.',
        ])
        self.assertEqual(result['decisions'], 'Rahul: We decided to keep the old export for now.')
        self.assertEqual(result['key_discussion_points'].splitlines(), [
            'Priya: Good morning everyone.',
            'Priya: The new dashboard is live?',
            'Arun: Yes, it went out yesterday.',
            'Arun: It will need some polish.',
        ], "a question keeps its question mark; 'it will' is no task")

    def test_parse_llm_summary(self):
        parsed = self.Summary._parse_llm_summary(json.dumps({
            'executive_summary': ['Point A', 'Point B'],
            'key_discussion_points': ['x', ' ', 'y'],
            'decisions': 'd1',
            'action_items': None,
        }))
        self.assertEqual(str(parsed['executive_summary']), '<p>Point A Point B</p>')
        self.assertEqual(parsed['key_discussion_points'], 'x\ny')
        self.assertEqual(parsed['decisions'], 'd1')
        self.assertEqual(parsed['action_items'], '')
        html = self.Summary._parse_llm_summary(json.dumps({'executive_summary': '<p>Done</p>'}))
        self.assertEqual(html['executive_summary'], '<p>Done</p>')
        escaped = self.Summary._parse_llm_summary(json.dumps({'executive_summary': 'a < b'}))
        self.assertEqual(str(escaped['executive_summary']), '<p>a &lt; b</p>')

    def test_generate_summary_requires_transcript(self):
        with self.assertRaises(UserError):
            self._meeting().action_generate_summary()

    def test_generate_summary_builtin(self):
        meeting = self._meeting(raw_transcript='Alice: We will ship on Monday.', ai_provider='internal')
        meeting.action_generate_summary()
        self.assertEqual(meeting.state, 'summarized')
        self.assertEqual(meeting.action_items, 'Alice: Will ship on Monday.')

    def test_generate_summary_openai(self):
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('meeting_transcription_summary.openai_api_key', 'sk-test')
        set_param('meeting_transcription_summary.openai_model', 'gpt-test')
        meeting = self._meeting(raw_transcript='Alice: We will ship on Monday.', ai_provider='openai')
        answer = {'executive_summary': 'Shipping plan.', 'key_discussion_points': ['Shipping'],
                  'decisions': ['Ship Monday'], 'action_items': ['Alice to ship']}
        reply = json_response({'choices': [{'message': {'content': json.dumps(answer)}}]})
        with patch(f'{SUMMARY_MODULE}.requests.post', return_value=reply) as post:
            meeting.action_generate_summary()
        self.assertEqual(post.call_args.kwargs['json']['model'], 'gpt-test')
        self.assertEqual(post.call_args.kwargs['headers'], {'Authorization': 'Bearer sk-test'})
        self.assertEqual(meeting.decisions, 'Ship Monday')
        self.assertEqual(meeting.action_items, 'Alice to ship')

    def test_generate_summary_openai_failure_falls_back(self):
        self.env['ir.config_parameter'].sudo().set_param('meeting_transcription_summary.openai_api_key', 'sk-test')
        meeting = self._meeting(raw_transcript='Alice: We will ship on Monday.', ai_provider='openai')
        with patch(f'{SUMMARY_MODULE}.requests.post', return_value=json_response({}, 500)), \
                self.assertLogs(SUMMARY_MODULE, 'WARNING'):
            meeting.action_generate_summary()
        self.assertEqual(meeting.action_items, 'Alice: Will ship on Monday.')

    def test_generate_summary_openai_without_key(self):
        meeting = self._meeting(raw_transcript='Alice: We will ship on Monday.', ai_provider='openai')
        with patch(f'{SUMMARY_MODULE}.requests.post') as post:
            meeting.action_generate_summary()
        post.assert_not_called()
        self.assertEqual(meeting.state, 'summarized')

    def test_generate_summary_ollama(self):
        self.env['ir.config_parameter'].sudo().set_param('meeting_transcription_summary.ollama_endpoint',
                                                         'http://ollama.test:11434/')
        meeting = self._meeting(raw_transcript='Bob: The budget is fine.', ai_provider='ollama')
        reply = json_response({'message': {'content': json.dumps({'executive_summary': 'Budget review.',
                                                                    'key_discussion_points': 'Budget'})}})
        with patch(f'{SUMMARY_MODULE}.requests.post', return_value=reply) as post:
            meeting.action_generate_summary()
        self.assertEqual(post.call_args.args[0], 'http://ollama.test:11434/api/chat')
        self.assertEqual(meeting.key_discussion_points, 'Budget')
        with patch(f'{SUMMARY_MODULE}.requests.post', side_effect=requests.ConnectionError('down')), \
                self.assertLogs(SUMMARY_MODULE, 'WARNING'):
            meeting.action_generate_summary()
        self.assertEqual(meeting.key_discussion_points, 'Bob: The budget is fine.')

    def test_post_summary_escapes_meeting_text(self):
        meeting = self._meeting(
            name='Review <script>alert(1)</script>', duration_minutes=1,
            executive_summary='<p>We reviewed <b>collections</b>.</p>',
            key_discussion_points='Volumes up\nGlass <img src=x onerror=alert(1)>',
            decisions='Add a driver', action_items='Priya: send reminder', state='summarized',
            attendee_ids=[(6, 0, self.alice.partner_id.ids)],
        )
        meeting.action_post_to_channel()
        body = self._last_message_body()
        self.assertEqual(meeting.state, 'posted')
        for label in ('Meeting Summary', 'Key Points', 'Decisions', 'Action Items', 'Priya: send reminder',
                      '1 min', 'Alice Martin', '>AM<', 'View full transcript', 'Copy summary'):
            self.assertIn(label, body)
        self.assertNotIn('No action items', body)
        # the copy link and its card keep their classes through the message sanitizer
        for css_class in ('o_meeting_summary_card', 'o_meeting_summary_body', 'o_meeting_summary_footer',
                          'o_meeting_summary_copy'):
            self.assertIn(css_class, body)
        self.assertIn(f'id={meeting.id}&amp;model=discuss.meeting.summary', body)
        self.assertIn('<b>collections</b>', body)
        self.assertNotIn('<script>', body)
        self.assertNotIn('<img', body)
        with self.assertRaises(UserError):
            meeting.action_post_to_channel()

    def test_post_summary_without_action_items(self):
        meeting = self._meeting(
            name='General', duration_minutes=58, executive_summary='<p>A short session.</p>',
            key_discussion_points='Greetings', state='summarized',
            date=fields.Datetime.to_datetime('2026-10-27 07:22:00'),
        )
        meeting.with_context(tz='Asia/Kolkata').action_post_to_channel()
        body = self._last_message_body()
        self.assertIn('58 min', body)
        self.assertIn('No action items were identified in this meeting.', body)
        self.assertIn('Oct 27, 2026 · 12:52', body)
        self.assertIn('1:50', body)

    def test_generate_and_post_once(self):
        meeting = self._meeting(raw_transcript='Alice: We will ship on Monday.', state='draft')
        meeting.action_generate_and_post_summary()
        self.assertEqual(meeting.state, 'posted')
        messages = len(self.channel.message_ids)
        meeting.action_generate_and_post_summary()  # a second click changes nothing
        self.assertEqual(len(self.channel.message_ids), messages)

    def test_call_ended_prompt_needs_channel_message(self):
        meeting = self._meeting(raw_transcript='a\nb\nc', duration_minutes=5)
        self.assertTrue(meeting._post_call_ended_prompt())
        body = self._last_message_body()
        self.assertIn('5 mins', body)
        self.assertIn('Speech turns transcribed:', body)


@tagged('post_install', '-at_install')
class TestMeetingRecording(MeetingTestCommon):
    """Uploaded recordings: queueing, the background job cron, completion."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audio = base64.b64encode(b'RIFF fake audio')

    def setUp(self):
        super().setUp()
        # the cron commits its progress: not inside a test transaction
        patcher = patch.object(type(self.env['ir.cron']), '_commit_progress', return_value=float('inf'))
        patcher.start()
        self.addCleanup(patcher.stop)

    def _recording(self, **vals):
        return self._meeting(recording_file=self.audio, recording_filename='meeting.wav', **vals)

    def test_queue_checks(self):
        with self.assertRaises(UserError):
            self._meeting().action_transcribe_and_summarize()
        with self.assertRaises(UserError):
            self._recording(state='processing')._queue_recording_transcription()
        self.env['ir.config_parameter'].sudo().set_param('meeting_transcription_summary.stt_engine', 'grok')
        with self.assertRaises(UserError):
            self._recording()._queue_recording_transcription()

    def test_queue_recording(self):
        meeting = self._recording(state='failed', processing_error='old error')
        self.assertTrue(meeting.with_user(self.alice).action_transcribe_and_summarize())
        self.assertEqual(meeting.state, 'processing')
        self.assertFalse(meeting.processing_error)
        self.assertFalse(meeting.processing_start_dt)
        self.assertEqual(meeting.requested_by_id, self.alice)
        self.assertIn(self.env.cr.dbname, meeting._job_dir())
        self.assertTrue(meeting._job_dir().endswith(str(meeting.id)))

    def test_start_job_request(self):
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('meeting_transcription_summary.keywords', 'Cybrosys, Kozhikode\nThrissur')
        meeting = self._recording(state='processing', attendee_ids=[(6, 0, self.alice.partner_id.ids)])
        with patch.object(stt_client, 'start_job') as start_job:
            meeting._start_recording_job()
        job_dir, request, audio, filename = start_job.call_args.args
        self.assertEqual(job_dir, meeting._job_dir())
        self.assertEqual(request['engine'], 'whisper')
        self.assertEqual(request['keywords'], ['Cybrosys', 'Kozhikode', 'Thrissur', 'Alice Martin'])
        self.assertNotIn('api_key', request)
        self.assertEqual((audio, filename), (b'RIFF fake audio', 'meeting.wav'))
        self.assertEqual(meeting.transcription_engine, 'whisper')
        self.assertTrue(meeting.processing_start_dt)

        set_param('meeting_transcription_summary.stt_engine', 'grok')
        set_param('meeting_transcription_summary.xai_api_key', 'xai-test')
        with patch.object(stt_client, 'start_job') as start_job:
            meeting._start_recording_job()
        self.assertEqual(start_job.call_args.args[1]['api_key'], 'xai-test')
        self.assertEqual(meeting.transcription_engine, 'grok')

    def test_cron_starts_one_local_job_at_a_time(self):
        first, second = self._recording(state='processing'), self._recording(state='processing')
        with patch.object(stt_client, 'start_job') as start_job:
            self.Summary._cron_process_recordings()
        self.assertEqual(start_job.call_count, 1)
        self.assertTrue(first.processing_start_dt)
        self.assertFalse(second.processing_start_dt, "waits for the running Whisper job")

    def test_cron_job_outcomes(self):
        self.env['ir.config_parameter'].sudo().set_param('meeting_transcription_summary.ai_provider', 'internal')
        now = fields.Datetime.now()
        running = self._recording(state='processing', processing_start_dt=now, transcription_engine='whisper')
        stuck = self._recording(state='processing', processing_start_dt=now - timedelta(hours=7))
        done = self._recording(state='processing', processing_start_dt=now, post_when_done=True,
                               requested_by_id=self.alice.id)
        lost = self._recording(state='processing', processing_start_dt=now)
        statuses = {
            running._job_dir(): ('running', None),
            stuck._job_dir(): ('running', None),
            done._job_dir(): ('done', {'text': 'Alice: We will ship on Monday.', 'duration': 150}),
            lost._job_dir(): ('failed', 'the transcription job was lost'),
        }
        with patch.object(stt_client, 'job_status', side_effect=lambda job_dir: statuses[job_dir]), \
                patch.object(stt_client, 'cancel_job') as cancel_job, \
                self.assertLogs(SUMMARY_MODULE, 'WARNING'):
            self.Summary._cron_process_recordings()
        self.assertEqual(running.state, 'processing')
        self.assertEqual(stuck.state, 'failed')
        self.assertIn('longer than 6 hours', stuck.processing_error)
        self.assertIn(stuck._job_dir(), [c.args[0] for c in cancel_job.call_args_list])
        self.assertEqual(done.state, 'posted')
        self.assertEqual(done.duration_minutes, 2)
        self.assertEqual(done.action_items, 'Alice: Will ship on Monday.')
        self.assertEqual(lost.state, 'failed')

    def test_cron_start_failure(self):
        meeting = self._recording(state='processing')
        with patch.object(stt_client, 'start_job', side_effect=OSError('disk full')), \
                self.assertLogs(SUMMARY_MODULE, 'ERROR'):
            self.Summary._cron_process_recordings()
        self.assertEqual(meeting.state, 'failed')
        self.assertIn('disk full', meeting.processing_error)

    def test_complete_without_speech(self):
        meeting = self._recording(state='processing', requested_by_id=self.alice.id)
        with patch.object(stt_client, 'cancel_job'):
            meeting._complete_recording_job({'text': '  '})
        self.assertEqual(meeting.state, 'failed')
        self.assertIn('Could not transcribe any speech', meeting.processing_error)

    def test_complete_engine_not_installed(self):
        meeting = self._recording(state='processing', transcription_engine='whisper')
        with patch.object(stt_client, 'cancel_job'), self.assertLogs(SUMMARY_MODULE, 'WARNING'):
            meeting._complete_recording_job({'error': 'not_installed: No module named faster_whisper'})
        self.assertEqual(meeting.state, 'failed')
        self.assertIn('pip install faster-whisper', meeting.processing_error)

    def test_complete_grok_error(self):
        meeting = self._recording(state='processing', transcription_engine='grok')
        with patch.object(stt_client, 'cancel_job'), self.assertLogs(SUMMARY_MODULE, 'WARNING'):
            meeting._complete_recording_job({'error': 'HTTP 401'})
        self.assertIn('Grok STT could not transcribe the recording: HTTP 401', meeting.processing_error)

    def test_complete_with_openai_fallback(self):
        meeting = self._recording(state='processing', transcription_engine='whisper')
        with patch.object(stt_client, 'cancel_job'), self.assertLogs(SUMMARY_MODULE, 'WARNING'), \
                patch.object(type(meeting), '_transcribe_with_openai', return_value='Bob: We agreed on March.'):
            meeting._complete_recording_job({'error': 'worker crashed'})
        self.assertEqual(meeting.state, 'summarized')
        self.assertEqual(meeting.decisions, 'Bob: We agreed on March.')

    def test_complete_openai_fallback_error(self):
        meeting = self._recording(state='processing', transcription_engine='whisper')
        with patch.object(stt_client, 'cancel_job'), self.assertLogs(SUMMARY_MODULE, 'WARNING'), \
                patch.object(type(meeting), '_transcribe_with_openai', side_effect=UserError('quota exceeded')):
            meeting._complete_recording_job({'error': 'worker crashed'})
        self.assertEqual((meeting.state, meeting.processing_error), ('failed', 'quota exceeded'))

    def test_complete_summarizing_failure_keeps_transcript(self):
        meeting = self._recording(state='processing', requested_by_id=self.alice.id)
        with patch.object(stt_client, 'cancel_job'), self.assertLogs(SUMMARY_MODULE, 'ERROR'), \
                patch.object(type(meeting), 'action_generate_summary', side_effect=ValueError('boom')):
            meeting._complete_recording_job({'text': 'Alice: hello'})
        self.assertEqual(meeting.state, 'draft')
        self.assertEqual(meeting.raw_transcript, 'Alice: hello')

    def test_transcribe_with_openai(self):
        meeting = self._recording()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        self.assertEqual(meeting._transcribe_with_openai(), '', "no key: no fallback")
        set_param('meeting_transcription_summary.openai_api_key', 'sk-test')
        self.assertEqual(meeting._transcribe_with_openai(), '', "a key for summaries only is not an opt-in")
        set_param('meeting_transcription_summary.stt_openai_fallback', 'True')
        set_param('meeting_transcription_summary.subtitles_language', 'fr-FR')
        with patch(f'{SUMMARY_MODULE}.requests.post', return_value=json_response({'text': ' Bonjour. '})) as post:
            self.assertEqual(meeting._transcribe_with_openai(), 'Bonjour.')
        self.assertEqual(post.call_args.kwargs['files']['language'], (None, 'fr'))
        with patch(f'{SUMMARY_MODULE}.requests.post', return_value=json_response({}, 500)), \
                self.assertLogs(SUMMARY_MODULE, 'WARNING'), self.assertRaises(UserError):
            meeting._transcribe_with_openai()
        with patch(f'{SUMMARY_MODULE}.requests.post', side_effect=requests.Timeout('slow')), \
                self.assertRaises(UserError):
            meeting._transcribe_with_openai()

    def test_unlink_cancels_running_job(self):
        meeting = self._recording(state='processing')
        job_dir = meeting._job_dir()
        with patch.object(stt_client, 'cancel_job') as cancel_job:
            meeting.unlink()
        cancel_job.assert_called_once_with(job_dir)


@tagged('post_install', '-at_install')
class TestMeetingSettings(TransactionCase):

    def test_settings_are_stored(self):
        settings = self.env['res.config.settings'].create({
            'meeting_stt_engine': 'whistle',
            'meeting_subtitles_default_language': 'fr-FR',
            'meeting_subtitles_keywords': 'Cybrosys',
        })
        settings.execute()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        self.assertEqual(get_param('meeting_transcription_summary.stt_engine'), 'whistle')
        self.assertEqual(get_param('meeting_transcription_summary.subtitles_language'), 'fr-FR')
        self.assertEqual(get_param('meeting_transcription_summary.keywords'), 'Cybrosys')

    def test_speech_workers_setting(self):
        settings = self.env['res.config.settings'].create({'meeting_stt_workers': 2})
        settings.execute()
        self.assertEqual(self.env['ir.config_parameter'].sudo().get_param('meeting_transcription_summary.stt_workers'), '2')
        for workers in (0, 5):
            with self.assertRaises(ValidationError):
                self.env['res.config.settings'].create({'meeting_stt_workers': workers})

    def test_debug_audio_deleted_when_turned_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = os.path.join(tmp, 'odoo_subtitle_debug')
            with patch(f'{SETTINGS_MODULE}.DEBUG_AUDIO_DIR', folder):
                self.env['res.config.settings'].create({'meeting_save_debug_audio': True}).execute()
                os.makedirs(folder)
                open(os.path.join(folder, 'clip.wav'), 'wb').close()
                self.env['res.config.settings'].create({'meeting_save_debug_audio': True}).execute()
                self.assertTrue(os.path.exists(folder), "kept while debug audio stays on")
                self.env['res.config.settings'].create({'meeting_save_debug_audio': False}).execute()
                self.assertFalse(os.path.exists(folder))

    def test_missing_engine_package(self):
        missing = {'whisper': 'faster-whisper', 'whistle': 'cactus-needle'}
        with patch.object(stt_client, 'missing_package', side_effect=missing.get):
            settings = self.env['res.config.settings'].create({'meeting_stt_engine': 'whisper'})
            self.assertIn('pip install faster-whisper', settings.meeting_stt_missing_package)
            settings.meeting_stt_engine = 'whistle'
            self.assertIn('pip install cactus-needle', settings.meeting_stt_missing_package)
            settings.meeting_stt_engine = 'cloud_whisper'
            self.assertIn('uploaded recordings', settings.meeting_stt_missing_package)
            settings.meeting_stt_engine = 'grok'
            self.assertFalse(settings.meeting_stt_missing_package, "Grok STT needs no local package")
        with patch.object(stt_client, 'missing_package', return_value=None):
            for engine in ('whisper', 'whistle', 'cloud_whisper'):
                settings.meeting_stt_engine = engine
                self.assertFalse(settings.meeting_stt_missing_package, engine)

    def test_main_language_never_auto(self):
        field = self.env['res.config.settings']._fields['meeting_main_language']
        options = [value for value, _label in field._description_selection(self.env)]
        self.assertIn('en-US', options)
        self.assertNotIn('auto', options)


@tagged('post_install', '-at_install')
class TestMeetingSummaryEdgeCases(MeetingTestCommon):
    """Paths the main scenarios don't take: a call ending after its summary was posted, a summary
    reused, a recording sent to OpenAI with auto-detection, empty speech turns."""

    def test_call_end_after_summary_posted(self):
        sessions = self._start_call(self.alice_member)
        meeting = self.Summary._get_live_meeting(self.channel)
        meeting.transcribe_enabled = True
        self.Summary._add_transcript_line(self.channel, self.alice_member, 'Alice Martin', 'We will send the report.')
        meeting.action_generate_summary()
        meeting.action_post_to_channel()
        self.Summary._add_transcript_line(self.channel, self.alice_member, 'Alice Martin', 'We agreed on March.')
        messages = self.channel.message_ids
        sessions.unlink()
        self.assertEqual(meeting.state, 'posted', "stays posted")
        self.assertEqual(len(meeting.raw_transcript.splitlines()), 2, "the full transcript is still kept")
        self.assertGreaterEqual(meeting.duration_minutes, 1)
        self.assertEqual(self.channel.message_ids, messages, "nothing posted when the call ends")

    def test_recording_openai_auto_language(self):
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('meeting_transcription_summary.openai_api_key', 'sk-test')
        set_param('meeting_transcription_summary.stt_openai_fallback', 'True')
        set_param('meeting_transcription_summary.subtitles_language', 'auto')
        meeting = self._meeting(recording_file=base64.b64encode(b'ID3 fake audio'))
        with patch(f'{SUMMARY_MODULE}.requests.post', return_value=json_response({'text': ' Hello. '})) as post:
            self.assertEqual(meeting._transcribe_with_openai(), 'Hello.')
        files = post.call_args.kwargs['files']
        self.assertNotIn('language', files, "left to OpenAI to detect")
        self.assertEqual(files['file'], ('recording.mp4', b'ID3 fake audio'), "a default name for the upload")

    def test_builtin_summarizer_skips_empty_turns(self):
        result = self.Summary._builtin_summarize("[10:00:01] Alice:\nBob: We agreed on March.")
        self.assertEqual(result['decisions'], 'Bob: We agreed on March.')
        self.assertEqual(result['key_discussion_points'], 'Bob: We agreed on March.')
        self.assertNotIn('Alice:', result['key_discussion_points'])

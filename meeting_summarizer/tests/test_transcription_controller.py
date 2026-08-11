# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################       

import base64
import json
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import ValidationError
import sys
from odoo.addons.meeting_summarizer.controller.transcription import TranscriptionController

def _controller_env_getter(self):
    try:
        transcription_module = sys.modules.get('odoo.addons.meeting_summarizer.controller.transcription')
        if transcription_module:    
            return transcription_module.request.env
    except Exception:
        pass
    raise AttributeError("env is not available")

TranscriptionController.env = property(_controller_env_getter)


def _make_openai_response(content):
    """Build a mock object mimicking the OpenAI ChatCompletion response
    shape used by controller.create_summary(): response.choices[0].message.content
    """
    mock_message = MagicMock()
    mock_message.content = content
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


@tagged('post_install', '-at_install')
class TestTranscriptionDataChunkStorage(TransactionCase):
    """get_transcription_file() route.

    Stores incremental transcription chunks in ir.config_parameter under
    key 'transcription_id_<id>'.
    """

    def setUp(self):
        super().setUp()
        from odoo.addons.meeting_summarizer.controller.transcription import (
            TranscriptionController,
        )
        self.controller = TranscriptionController()
        self.cache_key = 'transcription_id_501'
        self.env['ir.config_parameter'].sudo().set_param(self.cache_key, False)

    def test_returns_error_when_id_missing(self):
        """Calling without an 'id' must return an error dict and must
        NOT write anything to ir.config_parameter."""
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request:
            mock_request.env = self.env
            result = self.controller.get_transcription_file(
                data='hello', id=None)
        self.assertIn('error', result)

    def test_first_chunk_creates_new_list_in_config_parameter(self):
        """The first chunk for a given id must create a JSON list
        with exactly one entry in ir.config_parameter."""
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request:
            mock_request.env = self.env
            result = self.controller.get_transcription_file(
                data='First sentence.', id=501, userId=7, timestamp='2026-01-01T00:00:00')
        stored = self.env['ir.config_parameter'].sudo().get_param(self.cache_key)
        parsed = json.loads(stored)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['data'], 'First sentence.')
        self.assertEqual(result.get('message'), 'Data stored successfully')

    def test_second_chunk_appends_to_existing_list(self):
        """A second call with the same id must append to the
        existing list rather than overwriting it."""
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request:
            mock_request.env = self.env
            self.controller.get_transcription_file(
                data='First sentence.', id=501, userId=7)
            self.controller.get_transcription_file(
                data='Second sentence.', id=501, userId=7)
        stored = self.env['ir.config_parameter'].sudo().get_param(self.cache_key)
        parsed = json.loads(stored)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[1]['data'], 'Second sentence.')

    def test_response_contains_correct_cache_key(self):
        """The route response must include the cache_key in the
        format 'transcription_id_<id>'."""
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request:
            mock_request.env = self.env
            result = self.controller.get_transcription_file(
                data='Chunk text', id=501)
        self.assertEqual(result.get('cache_key'), self.cache_key)

    def test_chunk_preserves_userid_and_timestamp(self):
        """Stored chunk entries must preserve the userId and
        timestamp values passed in."""
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request:
            mock_request.env = self.env
            self.controller.get_transcription_file(
                data='Text', id=501, userId=42, timestamp='2026-06-16T10:00:00')
        stored = self.env['ir.config_parameter'].sudo().get_param(self.cache_key)
        parsed = json.loads(stored)
        self.assertEqual(parsed[0]['userId'], 42)
        self.assertEqual(parsed[0]['timestamp'], '2026-06-16T10:00:00')


@tagged('post_install', '-at_install')
class TestCreateTranscriptionFileSummary(TransactionCase):
    """get_cached_transcription_file() route.

    Builds the transcript + AI summary as ir.attachment records.
    """

    def setUp(self):
        super().setUp()
        from odoo.addons.meeting_summarizer.controller.transcription import (
            TranscriptionController,
        )
        self.controller = TranscriptionController()
        self.transcription_id = 777
        self.cache_key = f'transcription_id_{self.transcription_id}'
        chunks = [
            {'data': 'Welcome everyone to the meeting.', 'userId': 1, 'timestamp': 't1'},
            {'data': 'Let us discuss the Q3 roadmap.', 'userId': 2, 'timestamp': 't2'},
        ]
        self.env['ir.config_parameter'].sudo().set_param(
            self.cache_key, json.dumps(chunks))
        self.env['ir.config_parameter'].sudo().set_param(
            'meeting_summarizer.open_api_key', 'sk-test-key-123')

    def test_returns_error_when_id_missing(self):
        """Calling without an id must return an error dict."""
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request:
            mock_request.env = self.env
            result = self.controller.get_cached_transcription_file(id=None)
        self.assertIn('error', result)

    def test_returns_error_when_no_cached_data(self):
        """If no cached transcription data exists for the id, the
        route must return an error dict."""
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request:
            mock_request.env = self.env
            result = self.controller.get_cached_transcription_file(id=99999)
        self.assertIn('error', result)

    def test_raises_validation_error_when_api_key_missing(self):
        """If 'meeting_summarizer.open_api_key' is not configured,
        a ValidationError must be raised."""
        self.env['ir.config_parameter'].sudo().set_param(
            'meeting_summarizer.open_api_key', False)
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request:
            mock_request.env = self.env
            with self.assertRaises(ValidationError):
                self.controller.get_cached_transcription_file(id=self.transcription_id)

    def test_creates_transcription_and_summary_attachments(self):
        """On success, two ir.attachment records must be created —
        one for the transcript text, one for the AI summary."""
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request, \
             patch('odoo.addons.meeting_summarizer.controller.transcription.openai.OpenAI') as mock_openai_cls:
            mock_request.env = self.env
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = _make_openai_response(
                'Summary: Q3 roadmap discussed.')
            mock_openai_cls.return_value = mock_client

            result = self.controller.get_cached_transcription_file(id=self.transcription_id)

        self.assertTrue(result.get('success'))
        transcription = self.env['ir.attachment'].browse(result['transcriptionId'])
        summary = self.env['ir.attachment'].browse(result['summaryId'])
        self.assertTrue(transcription.exists())
        self.assertTrue(summary.exists())

    def test_transcription_attachment_contains_joined_chunk_text(self):
        """The transcription attachment's content must be the
        newline-joined text of all cached chunks."""
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request, \
             patch('odoo.addons.meeting_summarizer.controller.transcription.openai.OpenAI') as mock_openai_cls:
            mock_request.env = self.env
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = _make_openai_response('Summary text.')
            mock_openai_cls.return_value = mock_client

            result = self.controller.get_cached_transcription_file(id=self.transcription_id)

        transcription = self.env['ir.attachment'].browse(result['transcriptionId'])
        content = base64.b64decode(transcription.datas).decode('utf-8')
        self.assertIn('Welcome everyone to the meeting.', content)
        self.assertIn('Let us discuss the Q3 roadmap.', content)

    def test_summary_attachment_contains_ai_generated_text(self):
        """The summary attachment's content must match the text
        returned by the (mocked) OpenAI completion."""
        expected_summary = 'The team agreed on the Q3 roadmap priorities.'
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request, \
             patch('odoo.addons.meeting_summarizer.controller.transcription.openai.OpenAI') as mock_openai_cls:
            mock_request.env = self.env
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = _make_openai_response(
                expected_summary)
            mock_openai_cls.return_value = mock_client

            result = self.controller.get_cached_transcription_file(id=self.transcription_id)

        summary = self.env['ir.attachment'].browse(result['summaryId'])
        content = base64.b64decode(summary.datas).decode('utf-8')
        self.assertEqual(content, expected_summary)

    def test_falls_back_to_error_message_when_openai_call_fails(self):
        """If the OpenAI API call raises an exception, the summary
        attachment must still be created, containing a fallback error
        message instead of crashing the route."""
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request, \
             patch('odoo.addons.meeting_summarizer.controller.transcription.openai.OpenAI') as mock_openai_cls:
            mock_request.env = self.env
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception('Rate limit exceeded')
            mock_openai_cls.return_value = mock_client

            result = self.controller.get_cached_transcription_file(id=self.transcription_id)

        self.assertTrue(result.get('success'))
        summary = self.env['ir.attachment'].browse(result['summaryId'])
        content = base64.b64decode(summary.datas).decode('utf-8')
        self.assertIn('AI Summary could not be generated', content)

    def test_existing_attachments_are_updated_not_duplicated(self):
        """Calling the route a second time for the same id (with
        pre-existing attachments) must update them in place rather than
        creating duplicates."""
        existing_transcription = self.env['ir.attachment'].create({
            'name': f'transcription_id_{self.transcription_id}.txt',
            'datas': base64.b64encode(b'Old transcript'),
            'res_model': 'ir.attachment',
            'res_id': self.transcription_id,
            'type': 'binary',
            'mimetype': 'text/plain',
        })
        existing_summary = self.env['ir.attachment'].create({
            'name': f'summary_id_{self.transcription_id}.txt',
            'datas': base64.b64encode(b'Old summary'),
            'res_model': 'ir.attachment',
            'res_id': self.transcription_id,
            'type': 'binary',
            'mimetype': 'text/plain',
        })
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request, \
             patch('odoo.addons.meeting_summarizer.controller.transcription.openai.OpenAI') as mock_openai_cls:
            mock_request.env = self.env
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = _make_openai_response(
                'Updated summary.')
            mock_openai_cls.return_value = mock_client

            result = self.controller.get_cached_transcription_file(id=self.transcription_id)

        total_attachments = self.env['ir.attachment'].search_count([
            ('name', 'in', [
                f'transcription_id_{self.transcription_id}.txt',
                f'summary_id_{self.transcription_id}.txt',
            ]),
        ])
        self.assertEqual(
            total_attachments, 2,
            "Existing attachments must be updated, not duplicated",
        )
        self.assertEqual(result['transcriptionId'], existing_transcription.id)
        self.assertEqual(result['summaryId'], existing_summary.id)


@tagged('post_install', '-at_install')
class TestTranscriptionDataSummaryLookup(TransactionCase):
    """get_transcription_data_summary() route."""

    def setUp(self):
        super().setUp()
        from odoo.addons.meeting_summarizer.controller.transcription import (
            TranscriptionController,
        )
        self.controller = TranscriptionController()
        self.channel_id = 321
        self.transcription_att = self.env['ir.attachment'].create({
            'name': f'transcription_id_{self.channel_id}.txt',
            'datas': base64.b64encode(b'transcript'),
            'type': 'binary',
        })
        self.summary_att = self.env['ir.attachment'].create({
            'name': f'summary_id_{self.channel_id}.txt',
            'datas': base64.b64encode(b'summary'),
            'type': 'binary',
        })

    def test_returns_false_ids_when_channel_id_missing(self):
        """Without a channelId, both transcriptionId and summaryId
        must be returned as False."""
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request:
            mock_request.env = self.env
            result = self.controller.get_transcription_data_summary(channelId=False)
        self.assertFalse(result['transcriptionId'])
        self.assertFalse(result['summaryId'])

    def test_returns_correct_attachment_ids_for_channel(self):
        """With a valid channelId, the route must return the correct
        transcription and summary attachment IDs."""
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request:
            mock_request.env = self.env
            result = self.controller.get_transcription_data_summary(
                channelId=self.channel_id)
        self.assertEqual(result['transcriptionId'], self.transcription_att.id)
        self.assertEqual(result['summaryId'], self.summary_att.id)


@tagged('post_install', '-at_install')
class TestCreateSendTranscriptionRecord(TransactionCase):
    """get_send_transcription_id() route."""

    def setUp(self):
        super().setUp()
        from odoo.addons.meeting_summarizer.controller.transcription import (
            TranscriptionController,
        )
        self.controller = TranscriptionController()
        self.partner = self.env['res.partner'].create({'name': 'Wizard Partner'})
        self.attachment = self.env['ir.attachment'].create({
            'name': 'transcription_id_55.txt',
            'datas': base64.b64encode(b'data'),
            'type': 'binary',
        })

    def test_creates_send_mail_transcription_record(self):
        """The route must create a send.mail.transcription record
        and return its id."""
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request:
            mock_request.env = self.env
            record_id = self.controller.get_send_transcription_id(
                partnerIds=[self.partner.id],
                subject='Test Subject',
                email_body='<p>Body</p>',
                transcriptionId=self.attachment.id,
            )
        record = self.env['send.mail.transcription'].browse(record_id)
        self.assertTrue(record.exists())
        self.assertEqual(record.subject, 'Test Subject')

    def test_relinks_attachment_res_model_to_wizard(self):
        """When a transcriptionId is provided, the attachment's
        res_model/res_id must be updated to point to the new wizard record."""
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request:
            mock_request.env = self.env
            record_id = self.controller.get_send_transcription_id(
                partnerIds=[self.partner.id],
                subject='Subject',
                email_body='<p>Body</p>',
                transcriptionId=self.attachment.id,
            )
        self.attachment.invalidate_recordset()
        self.assertEqual(self.attachment.res_model, 'send.mail.transcription')
        self.assertEqual(self.attachment.res_id, record_id)


@tagged('post_install', '-at_install')
class TestCheckAutoMailSend(TransactionCase):
    """check_auto_mail_send() route."""

    def setUp(self):
        super().setUp()
        from odoo.addons.meeting_summarizer.controller.transcription import (
            TranscriptionController,
        )
        self.controller = TranscriptionController()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('meeting_summarizer.auto_mail_send', True)
        params.set_param('meeting_summarizer.select_user', 'all_attendees')

        self.channel = self.env['discuss.channel'].create({'name': 'Test Meeting'})
        self.member_user = self.env['res.users'].create({
            'name': 'Member User', 'login': 'member_user_tms@example.com',
        })
        self.env['discuss.channel.member'].create({
            'channel_id': self.channel.id,
            'partner_id': self.member_user.partner_id.id,
        })

    def test_returns_empty_list_when_auto_mail_send_disabled(self):
        """If 'auto_mail_send' is disabled, the route must return an
        empty participants list regardless of channel membership."""
        self.env['ir.config_parameter'].sudo().set_param(
            'meeting_summarizer.auto_mail_send', False)
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request:
            mock_request.env = self.env
            result = self.controller.check_auto_mail_send(channelId=self.channel.id)
        self.assertEqual(result, [])

    def test_returns_all_attendees_when_mode_is_all_attendees(self):
        """With select_user='all_attendees', the route must return
        participant entries for all internal-user channel members."""
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request:
            mock_request.env = self.env
            result = self.controller.check_auto_mail_send(channelId=self.channel.id)
        partner_ids = [p['partner_id'] for p in result]
        self.assertIn(self.member_user.partner_id.id, partner_ids)

    def test_returns_only_host_when_mode_is_host(self):
        """With select_user='host', the route must return only the
        channel creator's partner, even if other members are present."""
        self.env['ir.config_parameter'].sudo().set_param(
            'meeting_summarizer.select_user', 'host')
        with patch('odoo.addons.meeting_summarizer.controller.transcription.request', new=MagicMock()) as mock_request:
            mock_request.env = self.env
            result = self.controller.check_auto_mail_send(channelId=self.channel.id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['partner_id'], self.channel.create_uid.partner_id.id)
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
from unittest.mock import patch
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestSendMailTranscriptionFields(TransactionCase):
    """Field definition tests for SendMailTranscription.
    """

    def setUp(self):
        super().setUp()
        self.partner_a = self.env['res.partner'].create({
            'name': 'Attendee A', 'email': 'attendee.a@example.com',
        })
        self.partner_b = self.env['res.partner'].create({
            'name': 'Attendee B', 'email': 'attendee.b@example.com',
        })

    def _make_attachment(self, name='transcription_id_one.txt', content='hello world'):
        return self.env['ir.attachment'].create({
            'name': name,
            'datas': base64.b64encode(content.encode('utf-8')),
            'res_model': 'ir.attachment',
            'res_id': 0,
            'type': 'binary',
            'mimetype': 'text/plain',
        })

    # -----------------------------------------------------------------------
    # Model registration & field existence
    # -----------------------------------------------------------------------

    def test_model_is_registered_as_transient(self):
        """'send.mail.transcription' must be a registered
        TransientModel."""
        model_cls = type(self.env['send.mail.transcription'])
        self.assertTrue(
            model_cls._transient,
            "'send.mail.transcription' must be a TransientModel",
        )

    def test_partner_ids_field_is_many2many_to_res_partner(self):
        """'partner_ids' must be a Many2many field to res.partner."""
        field = self.env['send.mail.transcription']._fields.get('partner_ids')
        self.assertIsNotNone(field)
        self.assertIsInstance(field, fields.Many2many)
        self.assertEqual(field.comodel_name, 'res.partner')

    def test_subject_field_is_required_char(self):
        """'subject' must be a required Char field."""
        field = self.env['send.mail.transcription']._fields.get('subject')
        self.assertIsNotNone(field)
        self.assertIsInstance(field, fields.Char)
        self.assertTrue(field.required, "'subject' must be required")

    def test_email_body_field_is_required_html(self):
        """'email_body' must be a required Html field."""
        field = self.env['send.mail.transcription']._fields.get('email_body')
        self.assertIsNotNone(field)
        self.assertIsInstance(field, fields.Html)
        self.assertTrue(field.required, "'email_body' must be required")

    def test_transcription_attachment_ids_is_readonly_many2many(self):
        """'transcription_attachment_ids' must be a readonly
        Many2many field to ir.attachment."""
        field = self.env['send.mail.transcription']._fields.get(
            'transcription_attachment_ids')
        self.assertIsNotNone(field)
        self.assertIsInstance(field, fields.Many2many)
        self.assertEqual(field.comodel_name, 'ir.attachment')
        self.assertTrue(field.readonly)

    def test_summary_attachment_ids_is_readonly_many2many(self):
        """'summary_attachment_ids' must be a readonly Many2many
        field to ir.attachment."""
        field = self.env['send.mail.transcription']._fields.get(
            'summary_attachment_ids')
        self.assertIsNotNone(field)
        self.assertIsInstance(field, fields.Many2many)
        self.assertEqual(field.comodel_name, 'ir.attachment')
        self.assertTrue(field.readonly)

    def test_record_creation_with_minimal_required_fields(self):
        """A record must be creatable with only the required fields
        (subject, email_body) populated."""
        record = self.env['send.mail.transcription'].create({
            'subject': 'Meeting Recap',
            'email_body': '<p>Summary content</p>',
        })
        self.assertTrue(record.exists())
        self.assertEqual(record.subject, 'Meeting Recap')

    def test_partner_ids_accepts_multiple_recipients(self):
        """'partner_ids' must accept and store multiple recipient
        partners."""
        record = self.env['send.mail.transcription'].create({
            'subject': 'Multi-recipient Test',
            'email_body': '<p>Body</p>',
            'partner_ids': [(6, 0, [self.partner_a.id, self.partner_b.id])],
        })
        self.assertEqual(len(record.partner_ids), 2)
        self.assertIn(self.partner_a, record.partner_ids)
        self.assertIn(self.partner_b, record.partner_ids)


@tagged('post_install', '-at_install')
class TestActionSendTranscription(TransactionCase):
    """Functional tests for action_send_transcription().

    Source: meeting_summarizer/models/send_mail_transcription.py
    """

    def setUp(self):
        super().setUp()
        self.partner_a = self.env['res.partner'].create({
            'name': 'Recipient A', 'email': 'recipient.a@example.com',
        })
        self.partner_b = self.env['res.partner'].create({
            'name': 'Recipient B', 'email': 'recipient.b@example.com',
        })
        self.transcription_attachment = self.env['ir.attachment'].create({
            'name': 'transcription_id_nine_nine.txt',
            'datas': base64.b64encode(b'Full meeting transcript text'),
            'res_model': 'ir.attachment',
            'res_id': 0,
            'type': 'binary',
            'mimetype': 'text/plain',
        })
        self.summary_attachment = self.env['ir.attachment'].create({
            'name': 'summary_id_nine_nine.txt',
            'datas': base64.b64encode(b'Short meeting summary text'),
            'res_model': 'ir.attachment',
            'res_id': 0,
            'type': 'binary',
            'mimetype': 'text/plain',
        })

    def _make_record(self, partner_ids=None, transcription=None, summary=None):
        return self.env['send.mail.transcription'].create({
            'partner_ids': [(6, 0, partner_ids or [self.partner_a.id])],
            'subject': 'Test Meeting Transcription',
            'email_body': '<p>Please find the attached files.</p>',
            'transcription_attachment_ids': [
                (6, 0, [transcription.id])] if transcription else [],
            'summary_attachment_ids': [
                (6, 0, [summary.id])] if summary else [],
        })

    # -----------------------------------------------------------------------
    # email_template lookup and send_mail invocation
    # -----------------------------------------------------------------------

    def test_action_send_transcription_calls_send_mail_on_template(self):
        """action_send_transcription() must call send_mail() on the
        'meeting_summarizer.email_template_transcription' template with
        force_send=True."""
        record = self._make_record(
            transcription=self.transcription_attachment,
            summary=self.summary_attachment,
        )
        with patch(
            'odoo.addons.mail.models.mail_template.MailTemplate.send_mail'
        ) as mock_send_mail:
            record.action_send_transcription()
            self.assertTrue(mock_send_mail.called)
            _, kwargs = mock_send_mail.call_args
            self.assertTrue(kwargs.get('force_send'))

    def test_action_send_transcription_passes_correct_record_id(self):
        """send_mail() must be called with the transcription
        record's own ID as the first positional argument."""
        record = self._make_record()
        with patch(
            'odoo.addons.mail.models.mail_template.MailTemplate.send_mail'
        ) as mock_send_mail:
            record.action_send_transcription()
            args, _ = mock_send_mail.call_args
            self.assertEqual(args[0], record.id)

    def test_email_values_contain_correct_subject(self):
        """The email_values dict passed to send_mail() must contain
        the record's 'subject' field value."""
        record = self._make_record()
        with patch(
            'odoo.addons.mail.models.mail_template.MailTemplate.send_mail'
        ) as mock_send_mail:
            record.action_send_transcription()
            _, kwargs = mock_send_mail.call_args
            email_values = kwargs.get('email_values', {})
            self.assertEqual(email_values.get('subject'), record.subject)

    def test_email_values_contain_correct_body_html(self):
        """The email_values dict must contain 'body_html' matching
        the record's email_body."""
        record = self._make_record()
        with patch(
            'odoo.addons.mail.models.mail_template.MailTemplate.send_mail'
        ) as mock_send_mail:
            record.action_send_transcription()
            _, kwargs = mock_send_mail.call_args
            email_values = kwargs.get('email_values', {})
            self.assertIn('Please find the attached files', email_values.get('body_html', ''))

    # -----------------------------------------------------------------------
    # Recipient email aggregation
    # -----------------------------------------------------------------------

    def test_email_values_email_to_contains_single_recipient(self):
        """With a single partner, email_to must contain exactly that
        partner's email address."""
        record = self._make_record(partner_ids=[self.partner_a.id])
        with patch(
            'odoo.addons.mail.models.mail_template.MailTemplate.send_mail'
        ) as mock_send_mail:
            record.action_send_transcription()
            _, kwargs = mock_send_mail.call_args
            email_values = kwargs.get('email_values', {})
            self.assertEqual(email_values.get('email_to'), self.partner_a.email)

    def test_email_values_email_to_contains_multiple_recipients(self):
        """With two partners, email_to must be a comma-joined string
        containing both email addresses."""
        record = self._make_record(
            partner_ids=[self.partner_a.id, self.partner_b.id])
        with patch(
            'odoo.addons.mail.models.mail_template.MailTemplate.send_mail'
        ) as mock_send_mail:
            record.action_send_transcription()
            _, kwargs = mock_send_mail.call_args
            email_to = kwargs.get('email_values', {}).get('email_to', '')
            self.assertIn(self.partner_a.email, email_to)
            self.assertIn(self.partner_b.email, email_to)

    def test_email_values_email_from_is_current_user(self):
        """email_from in email_values must equal the current user's
        email address."""
        record = self._make_record()
        with patch(
            'odoo.addons.mail.models.mail_template.MailTemplate.send_mail'
        ) as mock_send_mail:
            record.action_send_transcription()
            _, kwargs = mock_send_mail.call_args
            email_values = kwargs.get('email_values', {})
            self.assertEqual(email_values.get('email_from'), self.env.user.email)

    # -----------------------------------------------------------------------
    # Attachment handling
    # -----------------------------------------------------------------------

    def test_attachment_ids_include_transcription_attachment(self):
        """email_values['attachment_ids'] must include a command for
        the transcription attachment."""
        record = self._make_record(transcription=self.transcription_attachment)
        with patch(
            'odoo.addons.mail.models.mail_template.MailTemplate.send_mail'
        ) as mock_send_mail:
            record.action_send_transcription()
            _, kwargs = mock_send_mail.call_args
            attachment_ids = kwargs.get('email_values', {}).get('attachment_ids', [])
            self.assertIn((4, self.transcription_attachment.id), attachment_ids)

    def test_attachment_ids_include_summary_attachment(self):
        """email_values['attachment_ids'] must include a command for
        the summary attachment."""
        record = self._make_record(summary=self.summary_attachment)
        with patch(
            'odoo.addons.mail.models.mail_template.MailTemplate.send_mail'
        ) as mock_send_mail:
            record.action_send_transcription()
            _, kwargs = mock_send_mail.call_args
            attachment_ids = kwargs.get('email_values', {}).get('attachment_ids', [])
            self.assertIn((4, self.summary_attachment.id), attachment_ids)

    def test_attachment_ids_empty_when_no_attachments_linked(self):
        """email_values['attachment_ids'] must be an empty list when
        no transcription or summary attachments are linked to the record."""
        record = self._make_record()
        with patch(
            'odoo.addons.mail.models.mail_template.MailTemplate.send_mail'
        ) as mock_send_mail:
            record.action_send_transcription()
            _, kwargs = mock_send_mail.call_args
            attachment_ids = kwargs.get('email_values', {}).get('attachment_ids', [])
            self.assertEqual(attachment_ids, [])
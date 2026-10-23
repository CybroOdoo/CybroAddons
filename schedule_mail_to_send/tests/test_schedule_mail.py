# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test suite for Schedule Mail to Send module."""

from datetime import datetime, timedelta
from unittest.mock import patch
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestScheduleMail(TransactionCase):
    """Test cases for scheduling and dispatching emails."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment: partners, attachments, activity type."""
        super().setUpClass()
        cls.activity_type = cls.env.ref(
            'schedule_mail_to_send.mail_activity_schedule'
        )
        cls.test_partner = cls.env['res.partner'].create({
            'name': 'Test Target Partner',
            'email': 'target@example.com',
        })
        cls.recipient = cls.env['res.partner'].create({
            'name': 'Recipient Partner',
            'email': 'recipient@example.com',
        })
        cls.attachment = cls.env['ir.attachment'].create({
            'name': 'test_doc.txt',
            'raw': b'Test file content',
            'res_model': 'mail.compose.message',
        })

    def test_01_onchange_schedule_time(self):
        """Verify onchange replaces seconds with zero."""
        wizard = self.env['mail.compose.message'].new({
            'schedule_time': datetime(2030, 5, 20, 14, 30, 45),
        })
        wizard._onchange_schedule_time()  # pylint: disable=protected-access
        self.assertEqual(wizard.schedule_time.second, 0)

    def test_02_schedule_mail_past_date_raises_user_error(self):
        """Scheduling in the past should raise a UserError."""
        past_time = fields.Datetime.now() - timedelta(hours=1)
        wizard = self.env['mail.compose.message'].create({
            'model': 'res.partner',
            'res_ids': f"[{self.test_partner.id}]",
            'subject': 'Past Schedule',
            'body': '<p>Past body</p>',
            'schedule_time': past_time,
        })
        with self.assertRaises(UserError):
            wizard.action_schedule_mail()

    def test_03_schedule_mail_missing_schedule_time_raises_user_error(self):
        """Scheduling without schedule_time should raise a UserError."""
        wizard = self.env['mail.compose.message'].create({
            'model': 'res.partner',
            'res_ids': f"[{self.test_partner.id}]",
            'subject': 'No Schedule Time',
            'body': '<p>No time</p>',
        })
        with self.assertRaises(UserError):
            wizard.action_schedule_mail()

    def test_04_schedule_mail_missing_model_or_record_raises_user_error(self):
        """Scheduling without a valid record should raise a UserError."""
        future_time = fields.Datetime.now() + timedelta(days=2)
        wizard = self.env['mail.compose.message'].create({
            'subject': 'No Record',
            'body': '<p>No record specified</p>',
            'schedule_time': future_time,
        })
        with self.assertRaises(UserError):
            wizard.action_schedule_mail()

    def test_05_action_schedule_mail_success(self):
        """Verify successful email scheduling, linking to record."""
        future_time = fields.Datetime.now() + timedelta(days=1)
        wizard = self.env['mail.compose.message'].create({
            'model': 'res.partner',
            'res_ids': f"[{self.test_partner.id}]",
            'subject': 'Follow Up Meeting',
            'body': '<p>Scheduled follow-up message content</p>',
            'schedule_time': future_time,
            'partner_ids': [fields.Command.link(self.recipient.id)],
            'attachment_ids': [fields.Command.link(self.attachment.id)],
        })
        res = wizard.action_schedule_mail()
        self.assertEqual(res, {'type': 'ir.actions.client', 'tag': 'reload'})

        activity = self.env['mail.activity'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.test_partner.id),
            ('activity_type_id', '=', self.activity_type.id),
        ])
        self.assertTrue(activity, "Planned activity should be created.")
        self.assertEqual(activity.summary, 'Follow Up Meeting')
        self.assertTrue(activity.schedule_mail_id)

        mail = self.env['mail.mail'].browse(activity.schedule_mail_id)
        self.assertTrue(mail.exists())
        self.assertEqual(mail.model, 'res.partner')
        self.assertEqual(mail.res_id, self.test_partner.id)
        self.assertEqual(mail.subject, 'Follow Up Meeting')
        self.assertIn(self.recipient, mail.recipient_ids)
        self.assertIn(self.attachment, mail.attachment_ids)
        self.assertTrue(mail.scheduled_user_tz)

    def test_06_action_send_scheduled_mail_cron(self):
        """Cron only sends mails created by module whose date arrived."""
        future_time = fields.Datetime.now() + timedelta(days=1)
        wizard = self.env['mail.compose.message'].create({
            'model': 'res.partner',
            'res_ids': f"[{self.test_partner.id}]",
            'subject': 'Cron Test Mail',
            'body': '<p>Cron mail body</p>',
            'schedule_time': future_time,
            'partner_ids': [fields.Command.link(self.recipient.id)],
        })
        wizard.action_schedule_mail()

        activity = self.env['mail.activity'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.test_partner.id),
            ('activity_type_id', '=', self.activity_type.id),
        ])
        mail = self.env['mail.mail'].browse(activity.schedule_mail_id)

        # Unrelated scheduled mail not linked to this module's activity
        unrelated_mail = self.env['mail.mail'].create({
            'subject': 'Unrelated Scheduled Mail',
            'body_html': '<p>Unrelated body</p>',
            'scheduled_date': fields.Datetime.now() - timedelta(minutes=10),
            'email_to': 'other@example.com',
        })

        # Scheduled date in future: action_send_scheduled_mail won't process it
        self.env['mail.compose.message'].action_send_scheduled_mail()
        self.assertTrue(activity.exists())

        # Fast-forward our scheduled mail's scheduled_date to the past
        mail.write({
            'scheduled_date': fields.Datetime.now() - timedelta(minutes=5),
        })

        sent_mail_ids = []

        def mock_send(records, *_args, **_kwargs):
            sent_mail_ids.extend(records.ids)
            for r in records:
                r.state = 'sent'
            return True

        with patch.object(type(mail), 'send', side_effect=mock_send,
                          autospec=True):
            self.env['mail.compose.message'].action_send_scheduled_mail()

        self.assertIn(mail.id, sent_mail_ids)
        self.assertNotIn(unrelated_mail.id, sent_mail_ids)
        self.assertEqual(mail.state, 'sent')
        self.assertEqual(unrelated_mail.state, 'outgoing')

        remaining_activity = self.env['mail.activity'].search([
            ('id', '=', activity.id),
        ])
        self.assertFalse(
            remaining_activity,
            "Activity should be closed after mail dispatch."
        )

    def test_07_cron_definition_exists(self):
        """Verify the cron job record is properly installed."""
        cron = self.env.ref(
            'schedule_mail_to_send.ir_cron_schedule_mail_action',
            raise_if_not_found=False,
        )
        self.assertTrue(cron, "Cron job record should exist.")
        self.assertEqual(cron.code, 'model.action_send_scheduled_mail()')

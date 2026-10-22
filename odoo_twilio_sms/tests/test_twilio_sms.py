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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TwilioCommon

CLIENT = 'odoo.addons.odoo_twilio_sms.models.twilio_account.Client'


@tagged('post_install', '-at_install')
class TestTwilioSms(TwilioCommon):
    """Tests for sending SMS to a group."""

    def _create_sms(self, **vals):
        """Create a Twilio SMS for the test group."""
        return self.env['twilio.sms'].create({
            'name': 'Promotion',
            'partner_id': self.group.id,
            'account_id': self.account.id,
            **({} if 'template_body_id' in vals else {'content': 'Big sale today'}),
            **vals,
        })

    def test_group_members(self):
        """Partners added to a group are linked to it."""
        self.assertEqual(self.group.contact_ids, self.partner_1 | self.partner_2)

    def test_partner_in_several_groups(self):
        """A contact can be a member of several groups."""
        other_group = self.env['twilio.sms.group'].create({
            'name': 'Suppliers',
            'contact_ids': [(4, self.partner_1.id)],
        })
        self.assertIn(self.partner_1, self.group.contact_ids)
        self.assertIn(self.partner_1, other_group.contact_ids)

    def test_template_fills_content(self):
        """Choosing a template copies its content."""
        sms = self._create_sms(template_body_id=self.template.id)
        self.assertEqual(sms.content, 'Hello from Odoo')

    def test_defaults(self):
        """A new SMS is a draft scheduled for today."""
        sms = self._create_sms()
        self.assertEqual(sms.state, 'draft')
        self.assertEqual(sms.scheduled_date, fields.Date.today())

    def test_confirm_sends_today(self):
        """Confirming an SMS scheduled today sends it to every member."""
        sms = self._create_sms()
        with patch(CLIENT) as client:
            client.return_value.messages.create.return_value.sid = 'SM123'
            sms.action_confirm_sms()
        calls = client.return_value.messages.create.call_args_list
        self.assertEqual(sorted(c.kwargs['to'] for c in calls),
                         ['+15552222222', '+15553333333'])
        self.assertTrue(all(c.kwargs['body'] == 'Big sale today' for c in calls))
        self.assertTrue(all(c.kwargs['from_'] == '+15550000000' for c in calls))
        self.assertEqual(sms.state, 'sent')

    def test_confirm_future_not_sent(self):
        """Confirming an SMS scheduled later only confirms it."""
        sms = self._create_sms(scheduled_date=fields.Date.today() + timedelta(days=1))
        with patch(CLIENT) as client:
            sms.action_confirm_sms()
        client.return_value.messages.create.assert_not_called()
        self.assertEqual(sms.state, 'confirm')

    def test_send_result(self):
        """A successful send returns a success notification."""
        sms = self._create_sms()
        with patch(CLIENT) as client:
            client.return_value.messages.create.return_value.sid = 'SM123'
            action = sms.send_sms(sms)
        self.assertEqual(action['params']['type'], 'success')

    def test_send_error(self):
        """When nobody receives the SMS it stays confirmed and lists the members."""
        sms = self._create_sms()
        sms.state = 'confirm'
        with patch(CLIENT) as client:
            client.return_value.messages.create.side_effect = Exception('Invalid number')
            action = sms.send_sms(sms)
        self.assertEqual(sms.state, 'confirm')
        self.assertEqual(action['params']['type'], 'danger')
        self.assertIn('Partner One', action['params']['message'])
        self.assertIn('Partner Two', action['params']['message'])

    def test_send_continues_after_failure(self):
        """A failed member does not stop the others from receiving the SMS."""
        sms = self._create_sms()
        with patch(CLIENT) as client:
            client.return_value.messages.create.side_effect = [Exception('Invalid number'), None]
            action = sms.send_sms(sms)
        self.assertEqual(client.return_value.messages.create.call_count, 2)
        self.assertEqual(sms.state, 'sent')
        self.assertEqual(action['params']['type'], 'warning')
        self.assertIn('Partner One', action['params']['message'])
        self.assertNotIn('Partner Two', action['params']['message'])

    def test_member_without_phone(self):
        """Members without phone are skipped and reported."""
        self.partner_2.phone = False
        sms = self._create_sms()
        with patch(CLIENT) as client:
            action = sms.send_sms(sms)
        client.return_value.messages.create.assert_called_once()
        self.assertEqual(sms.state, 'sent')
        self.assertIn('Partner Two', action['params']['message'])

    def test_confirm_group_without_phone(self):
        """A group without any phone number cannot be confirmed."""
        (self.partner_1 | self.partner_2).phone = False
        sms = self._create_sms()
        with self.assertRaises(UserError):
            sms.action_confirm_sms()
        self.assertEqual(sms.state, 'draft')

    def test_edit_content_keeps_template(self):
        """Editing the SMS text does not change the template."""
        sms = self._create_sms(template_body_id=self.template.id)
        sms.content = 'Changed text'
        self.assertEqual(self.template.content, 'Hello from Odoo')
        self.assertEqual(sms.content, 'Changed text')

    def test_custom_content_without_template(self):
        """Text typed without template is kept."""
        sms = self._create_sms()
        self.assertEqual(sms.content, 'Big sale today')

    def test_scheduled_send(self):
        """The scheduled action sends only confirmed SMS due today."""
        due = self._create_sms(state='confirm')
        draft = self._create_sms(name='Draft')
        later = self._create_sms(name='Later', state='confirm',
                                 scheduled_date=fields.Date.today() + timedelta(days=1))
        with patch(CLIENT) as client:
            client.return_value.messages.create.return_value.sid = 'SM123'
            self.env['twilio.sms'].send_sms_on_time()
        self.assertEqual(due.state, 'sent')
        self.assertEqual(draft.state, 'draft')
        self.assertEqual(later.state, 'confirm')
        self.assertEqual(client.return_value.messages.create.call_count, 2)

    def test_cron_exists(self):
        """The scheduled action calls send_sms_on_time."""
        cron = self.env.ref('odoo_twilio_sms.ir_cron_send_sms')
        self.assertIn('send_sms_on_time', cron.code)

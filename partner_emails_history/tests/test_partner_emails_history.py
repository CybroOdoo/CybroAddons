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
from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPartnerEmailsHistory(TransactionCase):
    """Tests for the partner email and SMS history smart buttons."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        partner_model = cls.env['res.partner'].with_context(
            mail_create_nolog=True, mail_create_nosubscribe=True)
        cls.partner = partner_model.create({
            'name': 'History Partner',
            'email': 'history.partner@example.com',
        })
        cls.other_partner = partner_model.create({
            'name': 'Other Partner',
            'email': 'other.partner@example.com',
        })
        cls.no_email_partner = partner_model.create({
            'name': 'No Email Partner',
        })
        message = cls.env['mail.message']
        # Sent by the partner
        cls.sent_message = message.create({
            'model': 'res.partner',
            'res_id': cls.other_partner.id,
            'message_type': 'comment',
            'body': 'Sent mail',
            'email_from': 'History Partner <history.partner@example.com>',
            'author_id': cls.partner.id,
        })
        # Received by the partner
        cls.received_message = message.create({
            'model': 'res.partner',
            'res_id': cls.partner.id,
            'message_type': 'comment',
            'body': 'Received mail',
            'email_from': 'Other Partner <other.partner@example.com>',
            'author_id': cls.other_partner.id,
            'partner_ids': [Command.link(cls.partner.id)],
        })
        cls.sms = cls.env['sms.sms'].create({
            'partner_id': cls.partner.id,
            'number': '+911234567890',
            'body': 'Hello',
        })

    def _set_history_settings(self, history, sms, email):
        """Store the history settings and reset the cached flags."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_str('partner_emails_history.default_is_history', history)
        params.set_str('partner_emails_history.default_is_sms_history', sms)
        params.set_str('partner_emails_history.default_is_email_history',
                       email)
        self.env.invalidate_all()

    def test_email_counts(self):
        """Sent and received emails are counted for the partner."""
        self.assertEqual(self.partner.send_email_count, 1)
        self.assertEqual(self.partner.received_email_count, 1)
        self.assertEqual(self.other_partner.send_email_count, 1)
        self.assertEqual(self.other_partner.received_email_count, 0)

    def test_email_counts_multiple_records(self):
        """The compute must work on several records without a singleton
        error."""
        partners = self.partner | self.other_partner | self.no_email_partner
        self.assertEqual(partners.mapped('send_email_count'), [1, 1, 0])
        self.assertEqual(partners.mapped('received_email_count'), [1, 0, 0])

    def test_email_counts_without_email(self):
        """A partner without an email must not match every message."""
        self.assertFalse(self.no_email_partner.email)
        self.assertEqual(self.no_email_partner.send_email_count, 0)
        self.assertEqual(self.no_email_partner.received_email_count, 0)

    def test_email_counts_new_record(self):
        """A record not yet saved has no history."""
        new_partner = self.env['res.partner'].new({'name': 'Draft Partner'})
        self.assertEqual(new_partner.send_email_count, 0)
        self.assertEqual(new_partner.received_email_count, 0)
        self.assertEqual(new_partner.sms_count, 0)

    def test_sms_count(self):
        """SMS are counted for the partner."""
        partners = self.partner | self.other_partner
        self.assertEqual(partners.mapped('sms_count'), [1, 0])

    def test_action_view_partner_sms(self):
        """The SMS button opens the SMS of the partner only."""
        action = self.partner.action_view_partner_sms()
        self.assertEqual(action['res_model'], 'sms.sms')
        self.assertEqual(action['domain'], [('partner_id', '=',
                                             self.partner.id)])
        records = self.env['sms.sms'].search(action['domain'])
        self.assertEqual(records, self.sms)

    def test_sent_email_history(self):
        """The sent emails button opens the emails sent by the partner."""
        action = self.partner.sent_email_history()
        self.assertEqual(action['res_model'], 'mail.message')
        records = self.env['mail.message'].search(action['domain'])
        self.assertIn(self.sent_message, records)
        self.assertNotIn(self.received_message, records)

    def test_sent_email_history_without_email(self):
        """Without an email the domain only relies on the author."""
        action = self.no_email_partner.sent_email_history()
        self.assertEqual(action['domain'],
                         [('author_id', '=', self.no_email_partner.id)])
        self.assertFalse(self.env['mail.message'].search(action['domain']))

    def test_received_email_history(self):
        """The received emails button opens the emails received."""
        action = self.partner.received_email_history()
        self.assertEqual(action['res_model'], 'mail.message')
        records = self.env['mail.message'].search(action['domain'])
        self.assertEqual(records, self.received_message)

    def test_show_history_flags(self):
        """The buttons visibility follows the settings."""
        self._set_history_settings(True, True, False)
        self.assertTrue(self.partner.is_show_sms)
        self.assertFalse(self.partner.is_show_emails)
        self._set_history_settings(True, False, True)
        self.assertFalse(self.partner.is_show_sms)
        self.assertTrue(self.partner.is_show_emails)

    def test_show_history_flags_apply_to_new_partners(self):
        """A partner created after the settings change gets the flags."""
        self._set_history_settings(True, True, True)
        partner = self.env['res.partner'].create({'name': 'Late Partner'})
        self.assertTrue(partner.is_show_sms)
        self.assertTrue(partner.is_show_emails)

    def test_master_toggle(self):
        """Nothing is shown when the master toggle is disabled."""
        self._set_history_settings(False, True, True)
        self.assertFalse(self.partner.is_show_sms)
        self.assertFalse(self.partner.is_show_emails)
        self._set_history_settings('False', True, True)
        self.assertFalse(self.partner.is_show_sms)
        self.assertFalse(self.partner.is_show_emails)

    def test_settings_stored(self):
        """The settings are stored in the system parameters."""
        settings = self.env['res.config.settings'].create({
            'is_history': True,
            'is_sms_history': True,
            'is_email_history': True,
        })
        settings.set_values()
        self.env.invalidate_all()
        self.assertTrue(self.partner.is_show_sms)
        self.assertTrue(self.partner.is_show_emails)
        settings = self.env['res.config.settings'].create({
            'is_history': True,
            'is_sms_history': False,
            'is_email_history': True,
        })
        settings.set_values()
        self.env.invalidate_all()
        self.assertFalse(self.partner.is_show_sms)
        self.assertTrue(self.partner.is_show_emails)

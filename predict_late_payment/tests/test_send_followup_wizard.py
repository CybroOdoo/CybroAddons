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
"""Test cases for send.followup.wizard."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSendFollowupWizard(TransactionCase):
    """Test suite for the AI follow-up communication wizard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner Wizard',
            'email': 'wizard_test@example.com',
            'phone': '+15551234567',
            'customer_rank': 1,
        })
        cls.score_rec = cls.env['payment.risk.score'].create({
            'partner_id': cls.partner.id,
            'score': 65.0,
            'followup_email': 'Dear Customer, this is your drafted payment reminder email.',
            'followup_suggestion': 'Immediate courtesy call recommended.',
        })

    def test_wizard_onchange_prefers_followup_email(self):
        """Test that selecting a risk score sets the wizard message to followup_email first."""
        wizard = self.env['send.followup.wizard'].new({
            'partner_id': self.partner.id,
            'risk_score_id': self.score_rec.id,
        })
        wizard._onchange_risk_score()
        self.assertIn('drafted payment reminder email', wizard.message)
        self.assertNotIn('Immediate courtesy call', wizard.message)

    def test_wizard_onchange_fallback_to_suggestion(self):
        """Test that if followup_email is absent, followup_suggestion is used."""
        partner_no_email = self.env['res.partner'].create({
            'name': 'Partner No Email',
            'email': 'no_email@example.com',
        })
        score_rec_no_email = self.env['payment.risk.score'].create({
            'partner_id': partner_no_email.id,
            'score': 45.0,
            'followup_email': False,
            'followup_suggestion': 'Send courtesy note.',
        })
        wizard = self.env['send.followup.wizard'].new({
            'partner_id': partner_no_email.id,
            'risk_score_id': score_rec_no_email.id,
        })
        wizard._onchange_risk_score()
        self.assertIn('Send courtesy note.', wizard.message)

    def test_wizard_action_send_with_attachments_and_sms(self):
        """Test sending follow-up email, attaching statement, and sending SMS."""
        wizard = self.env['send.followup.wizard'].create({
            'partner_id': self.partner.id,
            'risk_score_id': self.score_rec.id,
            'subject': 'Payment Follow-up Test',
            'message': '<p>Please process outstanding invoices.</p>',
            'send_email': True,
            'send_sms': True,
            'attach_statement': True,
        })
        action = wizard.action_send()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'display_notification')
        self.assertEqual(action['params']['type'], 'success')

        # Verify email was generated with attachment
        sent_mail = self.env['mail.mail'].search([
            ('subject', '=', 'Payment Follow-up Test')
        ], limit=1)
        self.assertTrue(sent_mail)
        self.assertEqual(sent_mail.email_to, self.partner.email)
        self.assertTrue(sent_mail.attachment_ids)
        self.assertTrue(any('Statement_of_Account' in att.name for att in sent_mail.attachment_ids))

        # Verify chatter message was posted
        messages = self.env['mail.message'].search([
            ('model', '=', 'res.partner'),
            ('res_id', '=', self.partner.id),
        ])
        self.assertTrue(messages)

    def test_compute_overdue_invoices(self):
        """Test overdue invoices computed field on wizard."""
        wizard = self.env['send.followup.wizard'].create({
            'partner_id': self.partner.id,
            'message': '<p>Overdue check</p>',
        })
        wizard._compute_overdue_invoices()
        self.assertIsNotNone(wizard.overdue_invoices)

        # Partner without partner_id
        wizard_no_partner = self.env['send.followup.wizard'].new({'message': '<p>None</p>'})
        wizard_no_partner._compute_overdue_invoices()
        self.assertFalse(wizard_no_partner.overdue_invoices)

    def test_generate_statement_html(self):
        """Test generating HTML statement of account."""
        wizard = self.env['send.followup.wizard'].create({
            'partner_id': self.partner.id,
            'message': '<p>Statement check</p>',
        })
        statement = wizard._generate_statement_html(self.partner)
        self.assertIn('Statement of Account', statement)
        self.assertIn(self.partner.name, statement)

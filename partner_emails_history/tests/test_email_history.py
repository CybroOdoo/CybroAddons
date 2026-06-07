# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
from odoo.tests import common


class TestPartnerEmailHistory(common.TransactionCase):
    def setUp(self):
        super(TestPartnerEmailHistory, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'test@example.com'
        })

    def test_email_and_sms_history(self):
        self.env['mail.message'].create({
            'email_from': self.partner.email,
            'message_type': 'comment',
            'body': 'Outbound Message'
        })
        self.env['mail.message'].create({
            'partner_ids': [(4, self.partner.id)],
            'message_type': 'comment',
            'body': 'Inbound Message'
        })
        self.partner._compute_email()
        self.assertEqual(self.partner.send_email_count, 1)
        self.assertEqual(self.partner.received_email_count, 1)
        self.env['sms.sms'].create({
            'partner_id': self.partner.id,
            'number': '1234567890',
            'body': 'Test SMS Content'
        })
        self.partner._compute_sms()
        self.assertEqual(self.partner.sms_count, 1)
        sms_action = self.partner.action_view_partner_sms()
        self.assertEqual(sms_action['domain'], [('partner_id', '=', self.partner.id)])
        sent_action = self.partner.sent_email_history()
        self.assertEqual(sent_action['domain'], [('email_from', 'ilike', self.partner.email)])
        received_action = self.partner.received_email_history()
        self.assertEqual(received_action['domain'], [('partner_ids', 'in', self.partner.id)])
        config = self.env['res.config.settings'].create({
            'is_sms_history': True,
            'is_email_history': True
        })
        config._onchange_show_history()
        self.assertTrue(self.partner.is_show_sms)
        self.assertTrue(self.partner.is_show_emails)

    def test_multiple_partners_isolation(self):
        partner_b = self.env['res.partner'].create({
            'name': 'Partner B',
            'email': 'b@example.com'
        })
        self.env['mail.message'].create({
            'email_from': self.partner.email,
            'message_type': 'comment',
            'body': 'Message for A'
        })
        self.env['mail.message'].create({
            'email_from': partner_b.email,
            'message_type': 'comment',
            'body': 'Message for B'
        })
        self.partner._compute_email()
        partner_b._compute_email()
        self.assertEqual(self.partner.send_email_count, 1)
        self.assertEqual(partner_b.send_email_count, 1)

    def test_no_data_scenarios(self):
        partner_c = self.env['res.partner'].create({
            'name': 'Partner C'
        })
        partner_c._compute_email()
        partner_c._compute_sms()
        self.assertEqual(partner_c.send_email_count, 0)
        self.assertEqual(partner_c.received_email_count, 0)
        self.assertEqual(partner_c.sms_count, 0)

    def test_partial_email_match(self):
        self.env['mail.message'].create({
            'email_from': 'TEST@EXAMPLE.COM',
            'message_type': 'comment',
            'body': 'Case Insensitive Match'
        })
        self.partner._compute_email()
        self.assertGreaterEqual(self.partner.send_email_count, 1)

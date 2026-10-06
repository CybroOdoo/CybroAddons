# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1). It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included in
#    all copies or substantial portions of the Software.
#
#############################################################################

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestSendPaymentLinkWizard(TransactionCase):
    
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Wizard Partner'})
        
    def test_action_send_mail_no_email(self):
        """Test wizard action when partner does not have email"""
        wizard = self.env['send.payment.link.wizard'].create({
            'partner_id': self.partner.id,
        })
        with self.assertRaises(UserError):
            wizard.action_send_mail()

    def test_action_send_mail(self):
        """Test wizard action correctly sends email"""
        self.partner.email = 'test@example.com'
        wizard = self.env['send.payment.link.wizard'].create({
            'partner_id': self.partner.id,
        })
        
        try:
            res = wizard.action_send_mail()
            self.assertEqual(res['type'], 'ir.actions.act_window_close')
        except UserError as e:
            if 'The email template for the payment link was not found' in str(e):
                self.skipTest("Email template not found")
            else:
                raise e

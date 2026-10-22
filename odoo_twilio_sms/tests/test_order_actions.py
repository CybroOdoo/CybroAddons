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
from odoo.tests import tagged

from .common import TwilioCommon


@tagged('post_install', '-at_install')
class TestOrderActions(TwilioCommon):
    """Tests for the Send SMS buttons on partners and orders."""

    def _assert_sms_action(self, action, partner):
        """Check the action opens the SMS wizard for the partner."""
        self.assertEqual(action['res_model'], 'sms.builder')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['context'], {'default_partner_id': partner.id})

    def test_partner_action(self):
        """Contacts have a Send Twilio SMS action opening the wizard."""
        action = self.env.ref('odoo_twilio_sms.action_res_partner_view_form')
        self.assertEqual(action.res_model, 'sms.builder')
        self.assertEqual(action.binding_model_id.model, 'res.partner')
        self.assertIn('default_partner_id', action.context)

    def test_sale_order_action(self):
        """The sale order button opens the wizard for the customer."""
        order = self.env['sale.order'].create({'partner_id': self.partner_1.id})
        self._assert_sms_action(order.action_twilio_sms(), self.partner_1)

    def test_purchase_order_action(self):
        """The purchase order button opens the wizard for the vendor."""
        order = self.env['purchase.order'].create({'partner_id': self.partner_2.id})
        self._assert_sms_action(order.action_purchase_twilio_sms(), self.partner_2)

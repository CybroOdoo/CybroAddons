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

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo import Command

@tagged('post_install', '-at_install')
class TestResPartner(AccountTestInvoicingCommon):
    
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.move1 = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_line_ids': [Command.create({
                'name': 'Test Line',
                'quantity': 1,
                'price_unit': 100.0,
                'tax_ids': [],
                'account_id': cls.company_data['default_account_revenue'].id,
            })],
        })
        cls.move1.action_post()
        cls.move2 = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_line_ids': [Command.create({
                'name': 'Test Line',
                'quantity': 1,
                'price_unit': 150.0,
                'tax_ids': [],
                'account_id': cls.company_data['default_account_revenue'].id,
            })],
        })
        cls.move2.action_post()

    def test_get_overdue_amls(self):
        """Test finding overdue account.move.line records"""
        amls = self.partner.get_overdue_amls()
        self.assertTrue(len(amls) >= 2)
        move_ids = amls.mapped('move_id')
        self.assertIn(self.move1, move_ids)
        self.assertIn(self.move2, move_ids)

    def test_get_consolidated_total_due(self):
        """Test getting total due of the partner for the company"""
        total_due = self.partner.get_consolidated_total_due(self.env.company)
        self.assertEqual(total_due, 250.0)

    def test_get_total_due_in_company_currency(self):
        """Test computing total due amount in current company's currency"""
        total_due = self.partner.get_total_due_in_company_currency()
        self.assertEqual(total_due, 250.0)

    def test_get_access_token(self):
        """Test generation of access token"""
        from unittest.mock import patch
        with patch('odoo.addons.partner_consolidated_payment_link.models.res_partner.payment_utils.generate_access_token') as mock_generate:
            mock_generate.return_value = 'mocked_token_string'
            token = self.partner.get_access_token(250.0, self.env.company.currency_id.id)
            self.assertEqual(token, 'mocked_token_string')
            mock_generate.assert_called_once_with(self.partner.id, 250.0, self.env.company.currency_id.id)

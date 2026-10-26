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
from odoo import fields
from odoo.tests import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestPartnerPayableReceivable(AccountTestInvoicingCommon):
    """Test cases for total payable and receivable computation on partner."""

    def test_default_values(self):
        """Test that a new partner without moves has 0.0 payable and credit."""
        partner = self.env['res.partner'].create({
            'name': 'Fresh Test Partner',
        })
        self.assertEqual(partner.partner_credit, 0.0)
        self.assertEqual(partner.partner_debit, 0.0)

    def test_customer_invoice_receivable(self):
        """Test that posting an out_invoice increases partner_credit."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Test Product',
                    'quantity': 1,
                    'price_unit': 500.0,
                    'account_id':
                        self.company_data['default_account_revenue'].id,
                }),
            ],
        })
        # Draft invoice should not affect credit
        self.assertEqual(self.partner_a.partner_credit, 0.0)

        invoice.action_post()
        self.partner_a.invalidate_recordset(
            ['partner_credit', 'partner_debit']
        )
        self.assertAlmostEqual(self.partner_a.partner_credit, 500.0)
        self.assertEqual(self.partner_a.partner_debit, 0.0)

    def test_vendor_bill_payable(self):
        """Test that posting an in_invoice increases partner_debit."""
        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner_b.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Test Expense',
                    'quantity': 1,
                    'price_unit': 300.0,
                    'account_id':
                        self.company_data['default_account_expense'].id,
                }),
            ],
        })
        bill.action_post()
        self.partner_b.invalidate_recordset(
            ['partner_credit', 'partner_debit']
        )
        self.assertEqual(self.partner_b.partner_credit, 0.0)
        self.assertAlmostEqual(self.partner_b.partner_debit, 300.0)

    def test_empty_recordset_compute(self):
        """Test compute method on empty recordset does not raise errors."""
        empty_partners = self.env['res.partner']
        empty_partners._compute_partner_credit()
        self.assertFalse(empty_partners)

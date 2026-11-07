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
from odoo import Command
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAccountMoveLine(TransactionCase):
    """Unit tests for the account.move.line model in copy_invoice_line."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Invoice Partner',
        })

        # Set up income and expense accounts
        cls.income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', cls.env.company.id),
        ], limit=1)
        if not cls.income_account:
            cls.income_account = cls.env['account.account'].create({
                'name': 'Test Income Account',
                'code': 'TESTINC4000',
                'account_type': 'income',
                'company_ids': [Command.link(cls.env.company.id)],
            })

        cls.expense_account = cls.env['account.account'].search([
            ('account_type', '=', 'expense'),
            ('company_ids', 'in', cls.env.company.id),
        ], limit=1)
        if not cls.expense_account:
            cls.expense_account = cls.env['account.account'].create({
                'name': 'Test Expense Account',
                'code': 'TESTEXP5000',
                'account_type': 'expense',
                'company_ids': [Command.link(cls.env.company.id)],
            })

        # Set up sale and purchase journals
        cls.sale_journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.env.company.id),
        ], limit=1)
        if not cls.sale_journal:
            cls.sale_journal = cls.env['account.journal'].create({
                'name': 'Customer Invoices',
                'code': 'TINV',
                'type': 'sale',
                'company_id': cls.env.company.id,
            })

        cls.purchase_journal = cls.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('company_id', '=', cls.env.company.id),
        ], limit=1)
        if not cls.purchase_journal:
            cls.purchase_journal = cls.env['account.journal'].create({
                'name': 'Vendor Bills',
                'code': 'TBILL',
                'type': 'purchase',
                'company_id': cls.env.company.id,
            })

        # Set up products
        cls.product_sale = cls.env['product.product'].create({
            'name': 'Test Sale Product',
            'type': 'consu',
            'list_price': 150.0,
            'property_account_income_id': cls.income_account.id,
        })
        cls.product_purchase = cls.env['product.product'].create({
            'name': 'Test Purchase Product',
            'type': 'consu',
            'standard_price': 80.0,
            'property_account_expense_id': cls.expense_account.id,
        })

        # Set up customer invoice
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'journal_id': cls.sale_journal.id,
            'invoice_line_ids': [
                Command.create({
                    'name': 'Test Invoice Line',
                    'product_id': cls.product_sale.id,
                    'quantity': 2.0,
                    'price_unit': 150.0,
                    'sequence': 10,
                    'account_id': cls.income_account.id,
                }),
            ],
        })
        cls.invoice_line = cls.invoice.invoice_line_ids

    def test_action_copy_line(self):
        """Test duplicating account move lines via action_copy_line."""
        # 1. Test single invoice line duplication
        initial_line_count = len(self.invoice.invoice_line_ids)
        self.assertEqual(initial_line_count, 1)
        initial_sequence = self.invoice_line.sequence

        self.invoice_line.action_copy_line()

        lines = self.invoice.invoice_line_ids
        self.assertEqual(len(lines), initial_line_count + 1)

        # Check duplicated line attributes and sequence
        new_line = lines - self.invoice_line
        self.assertEqual(len(new_line), 1)
        self.assertEqual(new_line.product_id, self.product_sale)
        self.assertEqual(new_line.quantity, 2.0)
        self.assertEqual(new_line.price_unit, 150.0)
        self.assertEqual(new_line.move_id, self.invoice)
        self.assertEqual(new_line.sequence, initial_sequence + 1)

        # 2. Test sequential duplication (max sequence calculation)
        new_line.action_copy_line()
        lines_after_second_copy = self.invoice.invoice_line_ids
        self.assertEqual(len(lines_after_second_copy), initial_line_count + 2)
        newest_line = lines_after_second_copy - lines
        self.assertEqual(len(newest_line), 1)
        self.assertEqual(newest_line.sequence, initial_sequence + 2)

        # 3. Test duplicate on multiple lines recordset
        lines_before_multi = self.invoice.invoice_line_ids
        count_before_multi = len(lines_before_multi)
        lines_before_multi.action_copy_line()
        self.assertEqual(len(self.invoice.invoice_line_ids), count_before_multi * 2)

        # 4. Test duplicate on vendor bill (in_invoice)
        vendor_bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'journal_id': self.purchase_journal.id,
            'invoice_line_ids': [
                Command.create({
                    'name': 'Test Bill Line',
                    'product_id': self.product_purchase.id,
                    'quantity': 5.0,
                    'price_unit': 80.0,
                    'sequence': 5,
                    'account_id': self.expense_account.id,
                }),
            ],
        })
        bill_line = vendor_bill.invoice_line_ids
        bill_line.action_copy_line()
        bill_lines = vendor_bill.invoice_line_ids
        self.assertEqual(len(bill_lines), 2)
        new_bill_line = bill_lines - bill_line
        self.assertEqual(len(new_bill_line), 1)
        self.assertEqual(new_bill_line.product_id, self.product_purchase)
        self.assertEqual(new_bill_line.quantity, 5.0)
        self.assertEqual(new_bill_line.price_unit, 80.0)
        self.assertEqual(new_bill_line.move_id, vendor_bill)
        self.assertEqual(new_bill_line.sequence, 6)

        # 5. Test line with default/zero sequence
        default_seq_invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'journal_id': self.sale_journal.id,
            'invoice_line_ids': [
                Command.create({
                    'name': 'Zero Sequence Line',
                    'product_id': self.product_sale.id,
                    'quantity': 1.0,
                    'price_unit': 100.0,
                    'sequence': 0,
                    'account_id': self.income_account.id,
                }),
            ],
        })
        zero_seq_line = default_seq_invoice.invoice_line_ids
        zero_seq_line.action_copy_line()
        all_lines = default_seq_invoice.invoice_line_ids
        self.assertEqual(len(all_lines), 2)
        copied_zero_line = all_lines - zero_seq_line
        self.assertEqual(copied_zero_line.sequence, 1)

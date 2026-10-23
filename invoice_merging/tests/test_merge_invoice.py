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
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMergeInvoice(TransactionCase):
    """Test suite for Invoice Merging wizard and operations"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_a = cls.env['res.partner'].create({
            'name': 'Test Partner A',
        })
        cls.partner_b = cls.env['res.partner'].create({
            'name': 'Test Partner B',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Service Product',
            'type': 'service',
            'list_price': 100.0,
        })

    def _create_invoice(self, move_type='out_invoice', partner=None, lines_count=1):
        """Helper to create draft invoices or bills with lines"""
        partner = partner or self.partner_a
        line_commands = [
            Command.create({
                'name': f'Test Line {i}',
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0 * (i + 1),
            })
            for i in range(lines_count)
        ]
        return self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': partner.id,
            'invoice_line_ids': line_commands,
        })

    def test_merge_into_target_cancel_others(self):
        """Test merging multiple invoices into an existing target invoice and canceling others"""
        inv1 = self._create_invoice(lines_count=1)
        inv2 = self._create_invoice(lines_count=2)
        initial_lines_count = len(inv1.invoice_line_ids)

        wizard = self.env['merge.invoice'].create({
            'invoice_ids': [Command.set([inv1.id, inv2.id])],
            'target_invoice_id': inv1.id,
            'merge_type': 'cancel',
        })
        action = wizard.action_merge_invoice()

        # Check action return format
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_id'), inv1.id)
        self.assertEqual(action.get('res_model'), 'account.move')
        self.assertIn((False, 'form'), action.get('views', []))

        # Check invoice states and lines
        self.assertEqual(inv1.state, 'draft')
        self.assertEqual(inv2.state, 'cancel')
        # Target should now contain original lines plus copied lines
        self.assertGreater(len(inv1.invoice_line_ids), initial_lines_count)
        self.assertIn('Merged', inv1.payment_reference)

    def test_merge_into_target_keep_others(self):
        """Test merging into an existing target invoice while keeping source invoices in draft"""
        inv1 = self._create_invoice(lines_count=1)
        inv2 = self._create_invoice(lines_count=1)

        wizard = self.env['merge.invoice'].create({
            'invoice_ids': [Command.set([inv1.id, inv2.id])],
            'target_invoice_id': inv1.id,
            'merge_type': 'keep',
        })
        wizard.action_merge_invoice()

        self.assertEqual(inv1.state, 'draft')
        self.assertEqual(inv2.state, 'draft')

    def test_merge_into_new_invoice(self):
        """Test merging customer invoices into a brand new invoice with specified partner"""
        inv1 = self._create_invoice(lines_count=1)
        inv2 = self._create_invoice(lines_count=1)

        wizard = self.env['merge.invoice'].create({
            'invoice_ids': [Command.set([inv1.id, inv2.id])],
            'target_invoice_id': False,
            'partner_id': self.partner_b.id,
            'merge_type': 'cancel',
        })
        action = wizard.action_merge_invoice()

        new_invoice_id = action.get('res_id')
        self.assertTrue(new_invoice_id)
        new_invoice = self.env['account.move'].browse(new_invoice_id)

        # Verify it is created as customer invoice, not miscellaneous journal entry
        self.assertEqual(new_invoice.move_type, 'out_invoice')
        self.assertEqual(new_invoice.partner_id, self.partner_b)
        self.assertEqual(new_invoice.state, 'draft')
        self.assertEqual(inv1.state, 'cancel')
        self.assertEqual(inv2.state, 'cancel')
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)

    def test_merge_vendor_bills_into_new_bill(self):
        """Test merging vendor bills preserves 'in_invoice' move_type"""
        bill1 = self._create_invoice(move_type='in_invoice', partner=self.partner_a)
        bill2 = self._create_invoice(move_type='in_invoice', partner=self.partner_a)

        wizard = self.env['merge.invoice'].create({
            'invoice_ids': [Command.set([bill1.id, bill2.id])],
            'target_invoice_id': False,
            'partner_id': self.partner_b.id,
        })
        action = wizard.action_merge_invoice()
        new_bill = self.env['account.move'].browse(action.get('res_id'))

        self.assertEqual(new_bill.move_type, 'in_invoice')
        self.assertEqual(new_bill.partner_id, self.partner_b)

    def test_validation_single_invoice_error(self):
        """Test error when only one invoice is selected"""
        inv1 = self._create_invoice()
        wizard = self.env['merge.invoice'].create({
            'invoice_ids': [Command.set([inv1.id])],
        })
        with self.assertRaises((UserError, AccessError)):
            wizard.action_merge_invoice()

    def test_validation_posted_invoice_error(self):
        """Test error when any selected invoice is already posted"""
        inv1 = self._create_invoice()
        inv2 = self._create_invoice()
        inv1.action_post()

        wizard = self.env['merge.invoice'].create({
            'invoice_ids': [Command.set([inv1.id, inv2.id])],
        })
        with self.assertRaises((UserError, AccessError)):
            wizard.action_merge_invoice()

    def test_validation_different_move_types_error(self):
        """Test error when selected moves have different types (invoice vs bill)"""
        inv = self._create_invoice(move_type='out_invoice')
        bill = self._create_invoice(move_type='in_invoice')

        wizard = self.env['merge.invoice'].create({
            'invoice_ids': [Command.set([inv.id, bill.id])],
        })
        with self.assertRaises((UserError, AccessError)):
            wizard.action_merge_invoice()

    def test_validation_empty_partner_error(self):
        """Test error when creating a new merged invoice without specifying a partner"""
        inv1 = self._create_invoice()
        inv2 = self._create_invoice()

        wizard = self.env['merge.invoice'].create({
            'invoice_ids': [Command.set([inv1.id, inv2.id])],
            'target_invoice_id': False,
            'partner_id': False,
        })
        with self.assertRaises(UserError):
            wizard.action_merge_invoice()

    def test_account_move_action_merge_invoice(self):
        """Test opening wizard from account.move recordset action"""
        inv1 = self._create_invoice()
        inv2 = self._create_invoice()
        moves = inv1 + inv2

        action = moves.action_merge_invoice()
        self.assertEqual(action.get('res_model'), 'merge.invoice')
        self.assertEqual(action.get('target'), 'new')
        wizard = self.env['merge.invoice'].browse(action.get('res_id'))
        self.assertEqual(set(wizard.invoice_ids.ids), set(moves.ids))

    def test_account_move_name_search_override(self):
        """Test account.move name_search with display_invoice_with_partner context"""
        inv = self._create_invoice()
        res = self.env['account.move'].with_context(
            display_invoice_with_partner=True
        ).name_search(name=inv.name or '')
        found_ids = [r[0] for r in res]
        self.assertIn(inv.id, found_ids)

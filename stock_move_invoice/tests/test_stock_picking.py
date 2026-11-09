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
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestStockPicking(TransactionCase):
    """Test cases for 'stock.picking' model in stock_move_invoice."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Picking Test Partner 1',
            'email': 'partner1@example.com',
        })
        cls.partner_2 = cls.env['res.partner'].create({
            'name': 'Picking Test Partner 2',
            'email': 'partner2@example.com',
        })
        cls.income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
        ], limit=1)
        if not cls.income_account:
            cls.income_account = cls.env['account.account'].search([], limit=1)
        cls.product = cls.env['product.product'].create({
            'name': 'Picking Test Product',
            'type': 'consu',
            'lst_price': 50.0,
            'property_account_income_id': cls.income_account.id if cls.income_account else False,
        })
        if cls.income_account:
            cls.product.categ_id.property_account_income_categ_id = cls.income_account.id
        cls.sale_journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.env.company.id),
        ], limit=1)
        cls.purchase_journal = cls.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('company_id', '=', cls.env.company.id),
        ], limit=1)
        cls.picking_type_out = cls.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('warehouse_id.company_id', '=', cls.env.company.id),
        ], limit=1)
        cls.picking_type_in = cls.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id.company_id', '=', cls.env.company.id),
        ], limit=1)
        # Set default journals in config parameters
        cls.env['ir.config_parameter'].sudo().set_str(
            'stock_move_invoice.customer_journal_id', str(cls.sale_journal.id)
        )
        cls.env['ir.config_parameter'].sudo().set_str(
            'stock_move_invoice.vendor_journal_id', str(cls.purchase_journal.id)
        )

    def _create_test_picking(self, picking_type, partner, is_return=False):
        """Helper to create a stock.picking with a single move."""
        return self.env['stock.picking'].create({
            'partner_id': partner.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'is_return': is_return,
            'move_ids': [Command.create({
                'description_picking': 'Test Stock Move',
                'product_id': self.product.id,
                'product_uom_qty': 2.0,
                'quantity': 2.0,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
            })],
        })

    def test__compute_invoice_count(self):
        """Test _compute_invoice_count computes number of associated account.move records."""
        picking = self._create_test_picking(self.picking_type_out, self.partner_1)
        picking._compute_invoice_count()
        self.assertEqual(picking.invoice_count, 0)
        # Create move linked to picking via transfer_ids
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_1.id,
            'journal_id': self.sale_journal.id,
            'transfer_ids': [Command.link(picking.id)],
        })
        picking._compute_invoice_count()
        self.assertEqual(picking.invoice_count, 1)
    test_compute_invoice_count = test__compute_invoice_count

    def test__create_return(self):
        """Test _create_return marks the returned picking as is_return=True."""
        picking = self._create_test_picking(self.picking_type_out, self.partner_1)
        returned_picking = picking._create_return()
        self.assertTrue(returned_picking.is_return)
    test_create_return = test__create_return

    def test_action_create_invoice(self):
        """Test action_create_invoice creates out_invoice or raises error if journal unconfigured."""
        picking = self._create_test_picking(self.picking_type_out, self.partner_1)
        # 1. Successful invoice creation with multiple moves
        self.env['stock.move'].create({
            'picking_id': picking.id,
            'description_picking': 'Test Stock Move 2',
            'product_id': self.product.id,
            'product_uom_qty': 3.0,
            'quantity': 3.0,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        })
        invoice = picking.action_create_invoice()
        self.assertTrue(invoice)
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(invoice.partner_id, self.partner_1)
        self.assertIn(picking, invoice.transfer_ids)
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        # 2. Raise UserError when customer_journal_id is not configured
        self.env['ir.config_parameter'].sudo().set_str(
            'stock_move_invoice.customer_journal_id', ''
        )
        with self.assertRaises(UserError):
            picking.action_create_invoice()
        # Restore configuration
        self.env['ir.config_parameter'].sudo().set_str(
            'stock_move_invoice.customer_journal_id', str(self.sale_journal.id)
        )

    def test_action_create_bill(self):
        """Test action_create_bill creates in_invoice or raises error if journal unconfigured."""
        picking = self._create_test_picking(self.picking_type_in, self.partner_1)
        # 1. Successful bill creation
        bill = picking.action_create_bill()
        self.assertTrue(bill)
        self.assertEqual(bill.move_type, 'in_invoice')
        self.assertEqual(bill.partner_id, self.partner_1)
        self.assertIn(picking, bill.transfer_ids)
        # 2. Raise UserError when vendor_journal_id is not configured
        self.env['ir.config_parameter'].sudo().set_str(
            'stock_move_invoice.vendor_journal_id', ''
        )
        with self.assertRaises(UserError):
            picking.action_create_bill()
        # Restore configuration
        self.env['ir.config_parameter'].sudo().set_str(
            'stock_move_invoice.vendor_journal_id', str(self.purchase_journal.id)
        )

    def test_action_create_customer_credit(self):
        """Test action_create_customer_credit creates out_refund."""
        picking = self._create_test_picking(self.picking_type_in, self.partner_1, is_return=True)
        # 1. Successful credit note creation
        credit_note = picking.action_create_customer_credit()
        self.assertTrue(credit_note)
        self.assertEqual(credit_note.move_type, 'out_refund')
        self.assertEqual(credit_note.partner_id, self.partner_1)
        self.assertIn(picking, credit_note.transfer_ids)
        # 2. Raise UserError when customer_journal_id is not configured
        self.env['ir.config_parameter'].sudo().set_str(
            'stock_move_invoice.customer_journal_id', ''
        )
        with self.assertRaises(UserError):
            picking.action_create_customer_credit()
        # Restore configuration
        self.env['ir.config_parameter'].sudo().set_str(
            'stock_move_invoice.customer_journal_id', str(self.sale_journal.id)
        )

    def test_action_create_vendor_credit(self):
        """Test action_create_vendor_credit creates in_refund."""
        picking = self._create_test_picking(self.picking_type_out, self.partner_1, is_return=True)
        # 1. Successful vendor credit note creation
        credit_note = picking.action_create_vendor_credit()
        self.assertTrue(credit_note)
        self.assertEqual(credit_note.move_type, 'in_refund')
        self.assertEqual(credit_note.partner_id, self.partner_1)
        self.assertIn(picking, credit_note.transfer_ids)
        # 2. Raise UserError when vendor_journal_id is not configured
        self.env['ir.config_parameter'].sudo().set_str(
            'stock_move_invoice.vendor_journal_id', ''
        )
        with self.assertRaises(UserError):
            picking.action_create_vendor_credit()
        # Restore configuration
        self.env['ir.config_parameter'].sudo().set_str(
            'stock_move_invoice.vendor_journal_id', str(self.purchase_journal.id)
        )

    def test_action_open_picking_invoice(self):
        """Test action_open_picking_invoice returns act_window action to related invoices."""
        picking = self._create_test_picking(self.picking_type_out, self.partner_1)
        action = picking.action_open_picking_invoice()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'account.move')
        self.assertEqual(action.get('domain'), [('transfer_ids', 'in', picking.id)])

    def test_action_create_multi_invoice_for_multi_transfer(self):
        """Test action_create_multi_invoice_for_multi_transfer handles batch pickings."""
        # 1. Mixed picking types raise UserError
        p_out = self._create_test_picking(self.picking_type_out, self.partner_1)
        p_in = self._create_test_picking(self.picking_type_in, self.partner_1)
        mixed_pickings = p_out | p_in
        with self.assertRaises(UserError):
            mixed_pickings.action_create_multi_invoice_for_multi_transfer()
        # 2. Outgoing pickings with same partner -> consolidated out_invoice
        p_out_1 = self._create_test_picking(self.picking_type_out, self.partner_1)
        p_out_2 = self._create_test_picking(self.picking_type_out, self.partner_1)
        batch_out_same = p_out_1 | p_out_2
        batch_out_same.action_create_multi_invoice_for_multi_transfer()
        invoice_same = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('transfer_ids', 'in', p_out_1.id),
        ], limit=1)
        self.assertTrue(invoice_same)
        self.assertIn(p_out_1, invoice_same.transfer_ids)
        self.assertIn(p_out_2, invoice_same.transfer_ids)
        # 3. Outgoing pickings with different partners -> individual invoices
        p_out_diff_1 = self._create_test_picking(self.picking_type_out, self.partner_1)
        p_out_diff_2 = self._create_test_picking(self.picking_type_out, self.partner_2)
        batch_out_diff = p_out_diff_1 | p_out_diff_2
        batch_out_diff.action_create_multi_invoice_for_multi_transfer()
        self.assertEqual(p_out_diff_1.invoice_count, 1)
        self.assertEqual(p_out_diff_2.invoice_count, 1)
        # 4. Incoming pickings with same partner -> consolidated in_invoice
        p_in_1 = self._create_test_picking(self.picking_type_in, self.partner_1)
        p_in_2 = self._create_test_picking(self.picking_type_in, self.partner_1)
        batch_in_same = p_in_1 | p_in_2
        batch_in_same.action_create_multi_invoice_for_multi_transfer()
        bill_same = self.env['account.move'].search([
            ('move_type', '=', 'in_invoice'),
            ('transfer_ids', 'in', p_in_1.id),
        ], limit=1)
        self.assertTrue(bill_same)
        self.assertIn(p_in_1, bill_same.transfer_ids)
        self.assertIn(p_in_2, bill_same.transfer_ids)
        # 5. Incoming pickings with different partners -> individual bills
        p_in_diff_1 = self._create_test_picking(self.picking_type_in, self.partner_1)
        p_in_diff_2 = self._create_test_picking(self.picking_type_in, self.partner_2)
        batch_in_diff = p_in_diff_1 | p_in_diff_2
        batch_in_diff.action_create_multi_invoice_for_multi_transfer()
        self.assertEqual(p_in_diff_1.invoice_count, 1)
        self.assertEqual(p_in_diff_2.invoice_count, 1)

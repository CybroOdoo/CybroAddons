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
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPickingInvoice(TransactionCase):
    """Test cases for 'picking.invoice' wizard model in stock_move_invoice."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Wizard Test Partner',
            'email': 'wizard_partner@example.com',
        })
        cls.income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
        ], limit=1)
        if not cls.income_account:
            cls.income_account = cls.env['account.account'].search([], limit=1)
        cls.product = cls.env['product.product'].create({
            'name': 'Wizard Test Product',
            'type': 'consu',
            'lst_price': 100.0,
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
        cls.env['ir.config_parameter'].sudo().set_str(
            'stock_move_invoice.customer_journal_id', str(cls.sale_journal.id)
        )
        cls.env['ir.config_parameter'].sudo().set_str(
            'stock_move_invoice.vendor_journal_id', str(cls.purchase_journal.id)
        )

    def _create_done_picking(self, picking_type, is_return=False):
        """Helper to create a stock.picking in done state with a move."""
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'is_return': is_return,
            'move_ids': [Command.create({
                'description_picking': 'Wizard Stock Move',
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'quantity': 1.0,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
            })],
        })
        # Set state directly to done for wizard test
        picking.write({'state': 'done'})
        return picking

    def test_action_picking_multi_invoice(self):
        """Test action_picking_multi_invoice creates invoices for done pickings based on type and return status."""
        # 1. Incoming picking (not return) -> in_invoice (bill)
        p_in = self._create_done_picking(self.picking_type_in, is_return=False)
        wizard_in = self.env['picking.invoice'].with_context(active_ids=[p_in.id]).create({})
        wizard_in.action_picking_multi_invoice()
        p_in.invalidate_recordset(['invoice_count'])
        self.assertEqual(p_in.invoice_count, 1)
        bill = self.env['account.move'].search([('transfer_ids', 'in', p_in.id)], limit=1)
        self.assertEqual(bill.move_type, 'in_invoice')
        # 2. Outgoing picking (not return) -> out_invoice (customer invoice)
        p_out = self._create_done_picking(self.picking_type_out, is_return=False)
        wizard_out = self.env['picking.invoice'].with_context(active_ids=[p_out.id]).create({})
        wizard_out.action_picking_multi_invoice()
        p_out.invalidate_recordset(['invoice_count'])
        self.assertEqual(p_out.invoice_count, 1)
        inv = self.env['account.move'].search([('transfer_ids', 'in', p_out.id)], limit=1)
        self.assertEqual(inv.move_type, 'out_invoice')
        # 3. Incoming return picking -> out_refund (customer credit note)
        p_in_return = self._create_done_picking(self.picking_type_in, is_return=True)
        wizard_in_ret = self.env['picking.invoice'].with_context(active_ids=[p_in_return.id]).create({})
        wizard_in_ret.action_picking_multi_invoice()
        p_in_return.invalidate_recordset(['invoice_count'])
        self.assertEqual(p_in_return.invoice_count, 1)
        cust_refund = self.env['account.move'].search([('transfer_ids', 'in', p_in_return.id)], limit=1)
        self.assertEqual(cust_refund.move_type, 'out_refund')
        # 4. Outgoing return picking -> in_refund (vendor credit note)
        p_out_return = self._create_done_picking(self.picking_type_out, is_return=True)
        wizard_out_ret = self.env['picking.invoice'].with_context(active_ids=[p_out_return.id]).create({})
        wizard_out_ret.action_picking_multi_invoice()
        p_out_return.invalidate_recordset(['invoice_count'])
        self.assertEqual(p_out_return.invoice_count, 1)
        vendor_refund = self.env['account.move'].search([('transfer_ids', 'in', p_out_return.id)], limit=1)
        self.assertEqual(vendor_refund.move_type, 'in_refund')
        # 5. Non-done picking (state != 'done') is ignored
        p_draft = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.picking_type_out.default_location_src_id.id,
            'location_dest_id': self.picking_type_out.default_location_dest_id.id,
        })
        wizard_draft = self.env['picking.invoice'].with_context(active_ids=[p_draft.id]).create({})
        wizard_draft.action_picking_multi_invoice()
        p_draft.invalidate_recordset(['invoice_count'])
        self.assertEqual(p_draft.invoice_count, 0)

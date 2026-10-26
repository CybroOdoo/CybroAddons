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
from odoo.tests import common, tagged
from odoo.exceptions import ValidationError
from odoo import fields


@tagged('post_install', '-at_install')
class TestReturnInvoiceBill(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner Customer',
        })
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Test Vendor Supplier',
        })
        cls.product_delivery = cls.env['product.product'].create({
            'name': 'Product Delivery Policy',
            'type': 'consu',
            'is_storable': True,
            'list_price': 100.0,
            'standard_price': 60.0,
            'invoice_policy': 'delivery',
        })
        cls.product_ordered = cls.env['product.product'].create({
            'name': 'Product Ordered Policy',
            'type': 'consu',
            'is_storable': True,
            'list_price': 200.0,
            'standard_price': 120.0,
            'invoice_policy': 'order',
        })

    def _setup_done_sale_picking(self, product, qty=5.0):
        """Helper to create a sale order, deliver, and post the customer invoice."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': qty,
                'price_unit': product.list_price,
            })]
        })
        so.action_confirm()

        picking = so.picking_ids
        for move in picking.move_ids:
            move.quantity = qty
        picking.button_validate()

        # Invoicing
        invoicing_wizard = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_ids': [so.id],
        }).create({})
        invoicing_wizard.create_invoices()
        invoice = so.invoice_ids.filtered(lambda i: i.move_type == 'out_invoice')
        invoice.action_post()
        return so, picking, invoice

    def _setup_done_purchase_picking(self, product, qty=5.0):
        """Helper to create a purchase order, receive products, and post vendor bill."""
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_qty': qty,
                'price_unit': product.standard_price,
            })]
        })
        po.button_confirm()

        picking = po.picking_ids
        for move in picking.move_ids:
            move.quantity = qty
        picking.button_validate()

        # Vendor Bill
        po.action_create_invoice()
        bill = po.invoice_ids.filtered(lambda i: i.move_type == 'in_invoice')
        bill.invoice_date = fields.Date.today()
        bill.action_post()
        return po, picking, bill

    def test_01_validation_edge_cases(self):
        """Test all edge cases and validation rules on return.move wizard."""
        so, picking, invoice = self._setup_done_sale_picking(self.product_delivery, qty=5.0)

        # 1. Test picking in non-done state fails
        draft_picking = self.env['stock.picking'].create({
            'picking_type_id': picking.picking_type_id.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        })
        with self.assertRaises(ValidationError):
            wizard = self.env['return.move'].create({'picking_id': draft_picking.id})
            wizard.action_apply_reverse_entry()

        # Open wizard from done picking
        action = picking.action_return_with_credit_note()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        wizard = self.env['return.move'].browse(action['res_id'])
        self.assertTrue(wizard.line_ids, "Delivered lines must be pre-populated")

        # 2. Test missing reason
        wizard.reason = False
        for line in wizard.line_ids:
            line.quantity = 1.0
        with self.assertRaises(ValidationError):
            wizard.action_apply_reverse_entry()

        # 3. Test empty reason string (whitespace only)
        wizard.reason = '   '
        with self.assertRaises(ValidationError):
            wizard.action_apply_reverse_entry()

        # 4. Test zero return quantity
        wizard.reason = 'Faulty screen'
        for line in wizard.line_ids:
            line.quantity = 0.0
        with self.assertRaises(ValidationError):
            wizard.action_apply_reverse_entry()

        # 5. Test negative return quantity
        wizard.line_ids[0].quantity = -2.0
        with self.assertRaises(ValidationError):
            wizard.action_apply_reverse_entry()

        # 6. Test return quantity exceeding delivered quantity
        wizard.line_ids[0].quantity = wizard.line_ids[0].quantity_done + 10.0
        with self.assertRaises(ValidationError):
            wizard.action_apply_reverse_entry()

    def test_02_sale_delivery_partial_return_and_credit_note(self):
        """Test partial return of delivered items and automated Credit Note generation."""
        so, picking, invoice = self._setup_done_sale_picking(self.product_delivery, qty=10.0)

        # Return 3 units out of 10
        action = picking.action_return_with_credit_note()
        wizard = self.env['return.move'].browse(action['res_id'])
        wizard.reason = 'Customer requested refund for 3 items'
        wizard.refund_date = fields.Date.today()
        wizard.auto_post = True
        wizard.line_ids[0].quantity = 3.0

        res = wizard.action_apply_reverse_entry()
        self.assertEqual(res.get('res_model'), 'account.move')

        credit_note = self.env['account.move'].browse(res['res_id'])
        self.assertEqual(credit_note.move_type, 'out_refund')
        self.assertEqual(credit_note.state, 'posted', "Credit Note should be auto-posted")
        self.assertEqual(credit_note.origin_picking_id, picking)
        self.assertTrue(credit_note.return_picking_id)
        self.assertEqual(credit_note.return_picking_id.state, 'done')

        # Check return quantities on return picking
        return_move = credit_note.return_picking_id.move_ids[0]
        self.assertEqual(return_move.quantity, 3.0)

        # Check smart button count on original picking
        self.assertGreaterEqual(picking.return_invoice_count, 1)

        # Test smart button action
        stat_action = picking.action_get_credit_note()
        self.assertIn(credit_note.id, stat_action['domain'][0][2])

    def test_03_purchase_receipt_return_and_debit_note(self):
        """Test receipt return of purchased items and automated Debit Note generation."""
        po, picking, bill = self._setup_done_purchase_picking(self.product_delivery, qty=6.0)

        # Return 2 units out of 6
        action = picking.action_return_with_debit_note()
        wizard = self.env['return.move'].browse(action['res_id'])
        wizard.reason = 'Damaged goods returned to vendor'
        wizard.refund_date = fields.Date.today()
        wizard.auto_post = True
        wizard.line_ids[0].quantity = 2.0

        res = wizard.action_apply_reverse_entry()
        self.assertEqual(res.get('res_model'), 'account.move')

        debit_note = self.env['account.move'].browse(res['res_id'])
        self.assertEqual(debit_note.move_type, 'in_refund')
        self.assertEqual(debit_note.state, 'posted', "Debit Note should be auto-posted")
        self.assertEqual(debit_note.origin_picking_id, picking)
        self.assertTrue(debit_note.return_picking_id)
        self.assertEqual(debit_note.return_picking_id.state, 'done')

        # Check smart button count on original receipt
        self.assertGreaterEqual(picking.return_invoice_count, 1)
        stat_action = picking.action_get_debit_note()
        self.assertIn(debit_note.id, stat_action['domain'][0][2])

    def test_04_auto_post_false_creates_draft_note(self):
        """Test that unchecking auto_post keeps the Credit Note in Draft state."""
        so, picking, invoice = self._setup_done_sale_picking(self.product_delivery, qty=4.0)

        action = picking.action_return_with_credit_note()
        wizard = self.env['return.move'].browse(action['res_id'])
        wizard.reason = 'Pending accountant approval'
        wizard.auto_post = False
        wizard.line_ids[0].quantity = 2.0

        res = wizard.action_apply_reverse_entry()
        credit_note = self.env['account.move'].browse(res['res_id'])
        self.assertEqual(credit_note.state, 'draft', "Credit Note should remain Draft when auto_post is False")

    def test_05_ordered_invoicing_policy_fallback_reversal(self):
        """Test fallback reversal for products invoiced on ordered quantities."""
        so, picking, invoice = self._setup_done_sale_picking(self.product_ordered, qty=5.0)

        action = picking.action_return_with_credit_note()
        wizard = self.env['return.move'].browse(action['res_id'])
        wizard.reason = 'Return under ordered policy'
        wizard.auto_post = True
        wizard.line_ids[0].quantity = 2.0

        res = wizard.action_apply_reverse_entry()
        credit_note = self.env['account.move'].browse(res['res_id'])
        self.assertEqual(credit_note.move_type, 'out_refund')
        self.assertEqual(credit_note.state, 'posted')
        self.assertEqual(credit_note.origin_picking_id, picking)

    def _deliver_sale_without_invoice(self, product, qty=3.0):
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {'product_id': product.id, 'product_uom_qty': qty, 'price_unit': 10.0})],
        })
        so.action_confirm()
        picking = so.picking_ids
        picking.move_ids.quantity = qty
        picking.button_validate()
        return so, picking

    def test_06_wizard_default_get_context_variants(self):
        """default_get resolves the picking from several context shapes and picks a journal."""
        so, picking, invoice = self._setup_done_sale_picking(self.product_delivery, qty=2.0)
        Wizard = self.env['return.move']
        for ctx in (
            {'active_id': picking.id},
            {'default_picking_id': [picking.id]},
            {'default_picking_id': [(6, 0, [picking.id])]},
        ):
            res = Wizard.with_context(**ctx).default_get(['picking_id', 'journal_id', 'line_ids'])
            self.assertEqual(res['picking_id'], picking.id)
            self.assertEqual(res['journal_id'], invoice.journal_id.id)
            self.assertTrue(res['line_ids'])

        po, rec_picking, bill = self._setup_done_purchase_picking(self.product_delivery, qty=2.0)
        res = Wizard.with_context(active_id=rec_picking.id).default_get(['picking_id', 'journal_id'])
        self.assertEqual(res['journal_id'], bill.journal_id.id)

    def test_07_wizard_default_journal_fallback_without_posted_invoice(self):
        """Journal falls back to the company sale journal when nothing is invoiced yet."""
        so, picking = self._deliver_sale_without_invoice(self.product_delivery)
        res = self.env['return.move'].with_context(active_id=picking.id).default_get(['journal_id'])
        self.assertTrue(res.get('journal_id'))
        action = picking.action_return_with_credit_note()
        wizard = self.env['return.move'].browse(action['res_id'])
        self.assertEqual(wizard.journal_id.type, 'sale')

    def test_08_wizard_requires_posted_invoice_or_bill(self):
        """Returns are refused when the linked order has no posted invoice/bill."""
        so, picking = self._deliver_sale_without_invoice(self.product_delivery)
        wizard = self.env['return.move'].browse(picking.action_return_with_credit_note()['res_id'])
        wizard.reason = 'No invoice yet'
        wizard.line_ids[0].quantity = 1.0
        with self.assertRaisesRegex(ValidationError, 'posted customer invoice'):
            wizard.action_apply_reverse_entry()

        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {'product_id': self.product_delivery.id, 'product_qty': 2.0, 'price_unit': 5.0})],
        })
        po.button_confirm()
        po.picking_ids.move_ids.quantity = 2.0
        po.picking_ids.button_validate()
        wizard = self.env['return.move'].browse(po.picking_ids.action_return_with_debit_note()['res_id'])
        wizard.reason = 'No bill yet'
        wizard.line_ids[0].quantity = 1.0
        with self.assertRaisesRegex(ValidationError, 'posted vendor bill'):
            wizard.action_apply_reverse_entry()

    def test_09_wizard_without_lines_is_refused(self):
        so, picking, invoice = self._setup_done_sale_picking(self.product_delivery, qty=2.0)
        wizard = self.env['return.move'].create({'picking_id': picking.id, 'line_ids': [(5, 0, 0)]})
        wizard.line_ids.unlink()
        wizard.reason = 'Nothing to return'
        with self.assertRaisesRegex(ValidationError, 'No items'):
            wizard.action_apply_reverse_entry()

    def test_10_onchange_picking_rebuilds_lines(self):
        so, picking, invoice = self._setup_done_sale_picking(self.product_delivery, qty=2.0)
        wizard = self.env['return.move'].new({'picking_id': picking.id})
        wizard._onchange_picking_id()
        self.assertEqual(wizard.line_ids.product_id, self.product_delivery)
        self.assertEqual(wizard.line_ids.quantity_done, 2.0)

    def test_11_adjust_refund_lines_and_partial_multi_line_return(self):
        """Unreturned products are dropped from the refund and sections are kept."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {'product_id': self.product_ordered.id, 'product_uom_qty': 4.0, 'price_unit': 20.0}),
                (0, 0, {'product_id': self.product_delivery.id, 'product_uom_qty': 4.0, 'price_unit': 10.0}),
            ],
        })
        so.action_confirm()
        picking = so.picking_ids
        picking.move_ids.quantity = 4.0
        picking.button_validate()
        wiz = self.env['sale.advance.payment.inv'].with_context(
            active_model='sale.order', active_ids=[so.id]).create({})
        wiz.create_invoices()
        so.invoice_ids.action_post()

        wizard = self.env['return.move'].browse(picking.action_return_with_credit_note()['res_id'])
        wizard.reason = 'Return only one product'
        for line in wizard.line_ids:
            line.quantity = 1.0 if line.product_id == self.product_ordered else 0.0
        # a line with zero quantity is invalid, so drop it before applying
        wizard.line_ids.filtered(lambda l: l.product_id == self.product_delivery).unlink()
        res = wizard.action_apply_reverse_entry()
        note = self.env['account.move'].browse(res['res_id'])
        self.assertEqual(note.invoice_line_ids.product_id, self.product_ordered)
        self.assertEqual(len(note.return_picking_id.move_ids), 1)

    def test_12_related_refund_moves_fallback_to_order(self):
        """Without directly linked notes the order's refunds are used."""
        so, picking, invoice = self._setup_done_sale_picking(self.product_delivery, qty=2.0)
        self.assertFalse(picking._get_related_refund_moves())
        refund = invoice._reverse_moves([{'ref': 'manual'}])
        self.assertEqual(picking._get_related_refund_moves(), refund)
        self.assertEqual(picking.action_get_credit_note()['domain'][0][2], refund.ids)

        po, rec_picking, bill = self._setup_done_purchase_picking(self.product_delivery, qty=2.0)
        debit = bill._reverse_moves([{'ref': 'manual'}])
        self.assertEqual(rec_picking._get_related_refund_moves(), debit)

        plain = self.env['stock.picking'].create({
            'picking_type_id': picking.picking_type_id.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        })
        self.assertFalse(plain._get_related_refund_moves())

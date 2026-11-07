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
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestDocumentLines(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.product = self.env['product.product'].create({
            'name': 'Barcode Product',
            'is_storable': True,
            'list_price': 100.0,
        })
        self.env['product.multiple.barcodes'].create({
            'product_multi_barcode': 'DOC123',
            'product_id': self.product.id,
        })

    def test_01_sale_order_line_barcode(self):
        """Test scanning barcode on Sale Order Line."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        line = self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'name': 'Test',
        })
        line.scan_barcode = 'DOC123'
        line._onchange_scan_barcode()
        self.assertEqual(line.product_id, self.product)

    def test_02_purchase_order_line_barcode(self):
        """Test scanning barcode on Purchase Order Line."""
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        line = self.env['purchase.order.line'].create({
            'order_id': purchase_order.id,
            'name': 'Test',
            'product_qty': 1.0,
            'price_unit': 50.0,
        })
        line.scan_barcode = 'DOC123'
        line._onchange_scan_barcode()
        self.assertEqual(line.product_id, self.product)

    def test_03_stock_move_barcode_propagation(self):
        """Test barcode propagation from Sale Line to Stock Move."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'scan_barcode': 'DOC123',
        })
        sale_order.action_confirm()
        picking = sale_order.picking_ids
        move = picking.move_ids
        self.assertEqual(move.scan_barcode, 'DOC123')

    def test_04_account_move_line_barcode_propagation(self):
        """Test barcode propagation from Purchase Line to Account Move Line."""
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        self.env['purchase.order.line'].create({
            'order_id': purchase_order.id,
            'product_id': self.product.id,
            'product_qty': 1.0,
            'price_unit': 50.0,
            'scan_barcode': 'DOC123',
        })
        purchase_order.button_confirm()
        # Create invoice
        action = purchase_order.with_context(create_bill=True).action_create_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        inv_line = invoice.invoice_line_ids.filtered(lambda line: line.product_id == self.product)
        self.assertEqual(inv_line.scan_barcode, 'DOC123')

    def test_05_account_move_line_barcode_onchange(self):
        """Test scanning barcode directly on invoice line."""
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        invoice = self.env['account.move'].new({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'journal_id': journal.id,
        })
        line = self.env['account.move.line'].new({
            'move_id': invoice,
            'scan_barcode': 'DOC123',
        })
        line._onchange_scan_barcode()
        self.assertEqual(line.product_id, self.product)
        self.assertTrue(line.name)

    def test_06_sale_order_line_warning_and_empty(self):
        """Test scan_barcode warning and empty barcode on sale line."""
        line = self.env['sale.order.line'].new({'scan_barcode': False})
        self.assertIsNone(line._onchange_scan_barcode())
        line.scan_barcode = 'NONEXISTENT'
        res = line._onchange_scan_barcode()
        self.assertIn('warning', res)

    def test_07_purchase_order_line_warning_and_empty(self):
        """Test scan_barcode warning and empty barcode on purchase line."""
        line = self.env['purchase.order.line'].new({'scan_barcode': False})
        self.assertIsNone(line._onchange_scan_barcode())
        line.scan_barcode = 'NONEXISTENT'
        res = line._onchange_scan_barcode()
        self.assertIn('warning', res)

    def test_08_account_move_line_warning_and_empty_and_write(self):
        """Test scan_barcode warning, empty barcode, and manual assignment on invoice line."""
        line = self.env['account.move.line'].new({'scan_barcode': False})
        self.assertIsNone(line._onchange_scan_barcode())
        line.scan_barcode = 'NONEXISTENT'
        res = line._onchange_scan_barcode()
        self.assertIn('warning', res)
        line.scan_barcode = 'DOC123'
        self.assertEqual(line.scan_barcode, 'DOC123')
        # Test account.move _get_lang on empty recordset
        self.assertTrue(self.env['account.move']._get_lang())

    def test_09_stock_move_onchange_and_write(self):
        """Test scan_barcode onchange, empty barcode, warning, and manual assignment on stock move."""
        move = self.env['stock.move'].new({'scan_barcode': False})
        self.assertIsNone(move._onchange_scan_barcode())
        move.scan_barcode = 'NONEXISTENT'
        res = move._onchange_scan_barcode()
        self.assertIn('warning', res)
        move.scan_barcode = 'DOC123'
        move._onchange_scan_barcode()
        self.assertEqual(move.product_id, self.product)
        self.assertEqual(move.scan_barcode, 'DOC123')

    def test_10_sale_order_line_prepare_invoice_line(self):
        """Test barcode added into invoice line vals on sale order line."""
        sale_order = self.env['sale.order'].create({'partner_id': self.partner.id})
        so_line = self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': self.product.id,
            'scan_barcode': 'DOC123',
        })
        inv_vals = so_line._prepare_invoice_line()
        self.assertEqual(inv_vals.get('scan_barcode'), 'DOC123')

    def test_11_stock_move_purchase_propagation(self):
        """Test barcode propagation from purchase line to stock move."""
        purchase_order = self.env['purchase.order'].create({'partner_id': self.partner.id})
        self.env['purchase.order.line'].create({
            'order_id': purchase_order.id,
            'product_id': self.product.id,
            'product_qty': 1.0,
            'price_unit': 10.0,
            'scan_barcode': 'DOC123',
        })
        purchase_order.button_confirm()
        picking = purchase_order.picking_ids
        move = picking.move_ids
        self.assertEqual(move.scan_barcode, 'DOC123')

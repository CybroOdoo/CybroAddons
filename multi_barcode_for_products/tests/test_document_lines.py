# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: AYANA KP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase

class TestDocumentLines(TransactionCase):

    def setUp(self):
        super(TestDocumentLines, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.product = self.env['product.product'].create({
            'name': 'Barcode Product',
            'type': 'consu',
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
        line = self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'scan_barcode': 'DOC123',
        })
        sale_order.action_confirm()
        picking = sale_order.picking_ids
        move = picking.move_ids
        # Trigger compute
        move._compute_scan_barcode()
        self.assertEqual(move.scan_barcode, 'DOC123')

    def test_04_account_move_line_barcode_propagation(self):
        """Test barcode propagation from Purchase Line to Account Move Line."""
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        line = self.env['purchase.order.line'].create({
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
        inv_line = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product)
        # Trigger compute
        inv_line._compute_scan_barcode()
        self.assertEqual(inv_line.scan_barcode, 'DOC123')

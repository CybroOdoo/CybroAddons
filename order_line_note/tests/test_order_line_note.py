# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Surya Gayathry TA(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging

from odoo.tests import common
_logger = logging.getLogger(__name__)

class TestOrderLineNote(common.TransactionCase):
    """Test cases for checking the propagation of notes from order lines to
    stock moves and invoices."""

    @classmethod
    def setUpClass(cls):
        super(TestOrderLineNote, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner'
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',  # Using consumable to ensure stock moves are generated if stock is installed
        })

    def test_01_sale_order_line_note(self):
        """Test propagation of note from Sale Order Line to Stock Move and Invoice Line"""
        # Create Sale Order
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_uom_qty': 1.0,
                'note': 'Test Sale Note',
            })],
        })

        # Confirm Sale Order
        sale_order.action_confirm()

        # Check Stock Move
        stock_move = self.env['stock.move'].search([
            ('sale_line_id', '=', sale_order.order_line[0].id)
        ])
        self.assertTrue(stock_move, "Stock move should be created for the sale order line")
        self.assertEqual(stock_move.note, 'Test Sale Note',
                         "Note should be propagated from Sale Order Line to Stock Move")

        # Create Invoice
        invoice = sale_order._create_invoices()
        self.assertTrue(invoice, "Invoice should be created")
        self.assertEqual(invoice.invoice_line_ids[0].note, 'Test Sale Note',
                         "Note should be propagated from Sale Order Line to Invoice Line")

    def test_02_purchase_order_line_note(self):
        """Test propagation of note from Purchase Order Line to Stock Move and Invoice Line"""
        # Create Purchase Order
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_qty': 1.0,
                'price_unit': 100.0,
                'note': 'Test Purchase Note',
            })],
        })

        # Confirm Purchase Order
        purchase_order.button_confirm()

        # Check Stock Move
        stock_move = self.env['stock.move'].search([
            ('purchase_line_id', '=', purchase_order.order_line[0].id)
        ])
        self.assertTrue(stock_move, "Stock move should be created for the purchase order line")
        self.assertEqual(stock_move.note, 'Test Purchase Note',
                         "Note should be propagated from Purchase Order Line to Stock Move")

        # Create Invoice
        invoice_action = purchase_order.action_create_invoice()
        invoice = self.env['account.move'].browse(invoice_action['res_id'])
        self.assertTrue(invoice, "Invoice should be created")
        self.assertEqual(invoice.invoice_line_ids[0].note, 'Test Purchase Note',
                         "Note should be propagated from Purchase Order Line to Invoice Line")

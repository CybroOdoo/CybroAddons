# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################


# -*- coding: utf-8 -*-

import logging

from odoo import fields
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestPurchaseOrder(TransactionCase):
    """Test cases for purchase.order functions."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()

        _logger.info("Setting up Purchase Order test data")

        cls.partner = cls.env['res.partner'].create({
            'name': 'Vendor',
        })

        template = cls.env['product.template'].create({
            'name': 'Purchase Product',
            'type': 'consu',
            'is_storable': True,
            'standard_price': 50.0,
            'list_price': 100.0,
        })
        cls.product = template.product_variant_id

    def test_button_confirm(self):
        """Test that note is copied to stock move on PO confirmation."""
        _logger.info("Starting test_button_confirm")

        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'name': 'PO Line',
                'product_id': self.product.id,
                'product_uom': self.product.uom_po_id.id,
                'product_qty': 1,
                'price_unit': 100,
                'date_planned': fields.Datetime.now(),
                'note': 'Purchase Note',
            })]
        })

        purchase_order.button_confirm()

        stock_move = self.env['stock.move'].search([
            ('purchase_line_id', '=', purchase_order.order_line.id)
        ], limit=1)

        self.assertTrue(stock_move, "No stock move found for PO line.")
        self.assertEqual(stock_move.note, 'Purchase Note')

        _logger.info("Completed test_button_confirm")

    def test_action_create_invoice(self):
        """Test that note is copied to invoice line after receiving and invoicing."""
        _logger.info("Starting test_action_create_invoice")

        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'name': 'Invoice Line',
                'product_id': self.product.id,
                'product_uom': self.product.uom_po_id.id,
                'product_qty': 1,
                'price_unit': 100,
                'date_planned': fields.Datetime.now(),
                'note': 'Invoice Note',
            })]
        })

        purchase_order.button_confirm()

        picking = purchase_order.picking_ids[0]
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty

        picking.with_context(
            skip_backorder=True,
            skip_sanity_check=True,
        ).button_validate()

        purchase_order.action_create_invoice()

        move_line = self.env['account.move.line'].search([
            ('purchase_line_id', '=', purchase_order.order_line.id)
        ], limit=1)

        self.assertTrue(move_line, "No account move line found for PO line.")
        self.assertEqual(move_line.note, 'Invoice Note')

        _logger.info("Completed test_action_create_invoice")


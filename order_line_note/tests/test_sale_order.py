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

import logging

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestSaleOrder(TransactionCase):
    """Test cases for sale.order functions."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()

        _logger.info("Setting up Sale Order test data")

        cls.partner = cls.env['res.partner'].create({
            'name': 'Customer',
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Sale Product',
            'type': 'consu',
            'is_storable': True,
            'list_price': 100.0,
        })

    def test_action_confirm(self):
        """Test that note is copied to stock move on SO confirmation."""
        _logger.info("Starting test_action_confirm")

        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom': self.product.uom_id.id,
                'product_uom_qty': 1,
                'price_unit': 100,
                'note': 'Sale Note',
            })]
        })

        sale_order.action_confirm()

        stock_move = self.env['stock.move'].search([
            ('sale_line_id', '=', sale_order.order_line.id)
        ], limit=1)

        self.assertTrue(stock_move, "No stock move found for SO line.")
        self.assertEqual(stock_move.note, 'Sale Note')

        _logger.info("Completed test_action_confirm")


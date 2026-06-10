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

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestSaleOrderLine(TransactionCase):
    """Test cases for sale.order.line functions."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()

        _logger.info("Setting up Sale Order Line test data")

        cls.partner = cls.env['res.partner'].create({
            'name': 'Customer',
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Invoice Product',
            'type': 'consu',
            'list_price': 100.0,
        })

    def test_prepare_invoice_line(self):
        """Test that note is included in prepared invoice line values."""
        _logger.info("Starting test_prepare_invoice_line")

        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom': self.product.uom_id.id,
                'product_uom_qty': 1,
                'price_unit': 100,
                'note': 'Invoice Note',
            })]
        })

        sale_order.action_confirm()

        order_line = sale_order.order_line[0]
        invoice_vals = order_line._prepare_invoice_line()

        self.assertEqual(
            invoice_vals.get('note'),
            'Invoice Note',
            "Note was not correctly propagated to invoice line values."
        )

        _logger.info("Completed test_prepare_invoice_line")


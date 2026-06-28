# -*- coding: utf-8 -*-

import logging

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestProductProduct(TransactionCase):

    def setUp(self):
        super().setUp()

        # Set configuration values
        self.env['ir.config_parameter'].sudo().set_param(
            'purchase_product_history.status',
            'purchase_order'
        )

        self.env['ir.config_parameter'].sudo().set_param(
            'purchase_product_history.limit',
            '5'
        )

        # Vendor
        self.vendor = self.env['res.partner'].create({
            'name': 'Test Vendor',
            'supplier_rank': 1,
        })

        # Product
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
        })

        # Purchase Order
        self.purchase_order = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
        })

        # Purchase Order Line
        self.po_line = self.env['purchase.order.line'].create({
            'order_id': self.purchase_order.id,
            'product_id': self.product.id,
            'name': 'Test POL',
            'product_qty': 2,
            'price_unit': 100,
            'date_planned': '2026-05-14 10:00:00',
        })

        # Confirm PO
        self.purchase_order.button_confirm()

    def test_compute_po_product_line_ids(self):
        """Test purchase history line creation"""

        _logger.info("=== TEST STARTED PRODUCT.PRODUCT===")

        # Call compute method
        self.product._compute_po_product_line_ids()

        history_lines = self.env[
            'purchase.product.history.line'
        ].search([
            ('product_history_id', '=', self.product.id)
        ])

        _logger.info(
            "History Lines Count: %s",
            len(history_lines)
        )

        # Assertions
        self.assertTrue(history_lines)

        self.assertEqual(
            history_lines[0].product_history_id.id,
            self.product.id
        )

        self.assertEqual(
            history_lines[0].price_unit,
            100
        )

        self.assertEqual(
            history_lines[0].product_qty,
            2
        )

        _logger.info("=== TEST PASSED PRODUCT.PRODUCT===")
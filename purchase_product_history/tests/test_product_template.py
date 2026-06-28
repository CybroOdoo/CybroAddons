# -*- coding: utf-8 -*-

import logging

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestProductTemplate(TransactionCase):

    def setUp(self):
        super().setUp()

        # Configuration Parameters
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

        # Product Template
        self.product_template = self.env['product.template'].create({
            'name': 'Test Template',
            'type': 'consu',
        })

        # Product Variant
        self.product = self.product_template.product_variant_id

        # Purchase Order
        self.purchase_order = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
        })

        # Purchase Order Line
        self.po_line = self.env['purchase.order.line'].create({
            'order_id': self.purchase_order.id,
            'product_id': self.product.id,
            'name': 'Template POL',
            'product_qty': 3,
            'price_unit': 150,
            'date_planned': '2026-05-14 10:00:00',
        })

        # Confirm Purchase Order
        self.purchase_order.button_confirm()

    def test_compute_po_history_line_ids(self):
        """Test template purchase history line creation"""

        _logger.info("=== TEST STARTED PRODUCT.TEMPLATE===")

        # Call compute method
        self.product_template._compute_po_history_line_ids()

        history_lines = self.env[
            'purchase.template.history.line'
        ].search([
            ('history_id', '=', self.product_template.id)
        ])

        _logger.info(
            "History Lines Count: %s",
            len(history_lines)
        )

        # Assertions
        self.assertTrue(history_lines)

        self.assertEqual(
            history_lines[0].history_id.id,
            self.product_template.id
        )

        self.assertEqual(
            history_lines[0].price_unit,
            150
        )

        self.assertEqual(
            history_lines[0].product_qty,
            3
        )

        _logger.info("=== TEST PASSED PRODUCT.TEMPLATE===")
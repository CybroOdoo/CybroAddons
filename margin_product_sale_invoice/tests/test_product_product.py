# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class _MarginProductSaleInvoiceProductCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.positive_template = cls.env['product.template'].create({
            'name': 'Margin Positive Product',
            'list_price': 200.0,
            'standard_price': 80.0,
        })
        cls.zero_template = cls.env['product.template'].create({
            'name': 'Margin Zero Price Product',
            'list_price': 0.0,
            'standard_price': 80.0,
        })
        cls.positive_variant = cls.positive_template.product_variant_id
        cls.zero_variant = cls.zero_template.product_variant_id


@tagged('-at_install', 'post_install')
class TestProductProductMargin(_MarginProductSaleInvoiceProductCommon):

    def test_compute_margin_positive_value(self):
        self.assertAlmostEqual(self.positive_variant.margin_percent_product, 0.6)

    def test_compute_margin_zero_price(self):
        self.assertEqual(self.zero_variant.margin_percent_product, 0.0)

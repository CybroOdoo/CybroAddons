# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class _MarginProductSaleInvoiceTemplateCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
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


@tagged('-at_install', 'post_install')
class TestProductTemplateMargin(_MarginProductSaleInvoiceTemplateCommon):

    def test_compute_margin_positive_value(self):
        self.assertAlmostEqual(self.positive_template.margin_percent_product, 0.6)

    def test_compute_margin_zero_price(self):
        self.assertEqual(self.zero_template.margin_percent_product, 0.0)

# -*- coding: utf-8 -*-

from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class _MarginProductSaleInvoiceSaleCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.currency = cls.company.currency_id
        cls.partner = cls.env['res.partner'].create({
            'name': 'Margin Test Customer',
        })
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
        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Margin Pricelist',
            'currency_id': cls.currency.id,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'pricelist_id': cls.pricelist.id,
            'company_id': cls.company.id,
            'currency_id': cls.currency.id,
        })
        cls.sale_order.order_line = [
            Command.create({
                'product_id': cls.positive_variant.id,
                'product_uom_qty': 2.0,
                'price_unit': 200.0,
            }),
        ]
        cls.sale_order_zero = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'pricelist_id': cls.pricelist.id,
            'company_id': cls.company.id,
            'currency_id': cls.currency.id,
        })
        cls.sale_order_zero.order_line = [
            Command.create({
                'display_type': 'line_note',
                'name': 'Margin note line',
                'product_uom_qty': 0.0,
                'price_unit': 0.0,
            }),
        ]


@tagged('-at_install', 'post_install')
class TestSaleOrderMargin(_MarginProductSaleInvoiceSaleCommon):

    def test_compute_cost_price_and_margin_amount(self):
        line = self.sale_order.order_line[0]

        self.assertAlmostEqual(line.cost_price_sale, 80.0)
        self.assertAlmostEqual(line.margin_amount_sale, 240.0)
        self.assertAlmostEqual(self.sale_order.margin_amount_sale_total, 240.0)
        self.assertAlmostEqual(
            self.sale_order.margin_percent_sale,
            self.sale_order.margin_amount_sale_total / self.sale_order.amount_total,
        )

    def test_zero_price_line_and_order_margin(self):
        line = self.sale_order_zero.order_line[0]

        self.assertEqual(line.cost_price_sale, 0.0)
        self.assertEqual(line.margin_amount_sale, 0.0)
        self.assertEqual(self.sale_order_zero.margin_amount_sale_total, 0.0)
        self.assertEqual(self.sale_order_zero.margin_percent_sale, 0.0)

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleReport(TransactionCase):
    """Test cases for sale.report model extension in product_brand_sale module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.ProductBrand = cls.env['product.brand']
        cls.ProductTemplate = cls.env['product.template']
        cls.ProductProduct = cls.env['product.product']
        cls.SaleOrder = cls.env['sale.order']
        cls.SaleReport = cls.env['sale.report']

        cls.partner = cls.Partner.create({'name': 'Customer Test'})
        cls.brand_x = cls.ProductBrand.create({'name': 'Brand X'})
        cls.brand_y = cls.ProductBrand.create({'name': 'Brand Y'})

        cls.tmpl_x = cls.ProductTemplate.create({
            'name': 'Product Brand X',
            'brand_id': cls.brand_x.id,
            'list_price': 100.0,
        })
        cls.product_x = cls.tmpl_x.product_variant_id

        cls.tmpl_y = cls.ProductTemplate.create({
            'name': 'Product Brand Y',
            'brand_id': cls.brand_y.id,
            'list_price': 200.0,
        })
        cls.product_y = cls.tmpl_y.product_variant_id

        cls.tmpl_none = cls.ProductTemplate.create({
            'name': 'Product Without Brand',
            'list_price': 50.0,
        })
        cls.product_none = cls.tmpl_none.product_variant_id

    def test_01_sale_report_brand_populated(self):
        """Test that brand_id is correctly populated in sale.report from sale order lines."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({'product_id': self.product_x.id, 'product_uom_qty': 2}),
                Command.create({'product_id': self.product_y.id, 'product_uom_qty': 3}),
                Command.create({'product_id': self.product_none.id, 'product_uom_qty': 1}),
            ],
        })
        order.action_confirm()
        self.env['sale.order.line'].flush_recordset()

        # Check sale.report records
        reports_x = self.SaleReport.sudo().search([
            ('order_reference', '=', f'sale.order,{order.id}'),
            ('product_id', '=', self.product_x.id),
        ])
        self.assertTrue(reports_x, "Sale report for product X should exist.")
        self.assertEqual(reports_x.brand_id, self.brand_x, "Brand X should be set on report line.")

        reports_y = self.SaleReport.sudo().search([
            ('order_reference', '=', f'sale.order,{order.id}'),
            ('product_id', '=', self.product_y.id),
        ])
        self.assertTrue(reports_y, "Sale report for product Y should exist.")
        self.assertEqual(reports_y.brand_id, self.brand_y, "Brand Y should be set on report line.")

        reports_none = self.SaleReport.sudo().search([
            ('order_reference', '=', f'sale.order,{order.id}'),
            ('product_id', '=', self.product_none.id),
        ])
        self.assertTrue(reports_none, "Sale report for product without brand should exist.")
        self.assertFalse(reports_none.brand_id, "Brand should be False for product without brand.")

    def test_02_sale_report_groupby_brand(self):
        """Test grouping sale.report by brand_id."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({'product_id': self.product_x.id, 'product_uom_qty': 5}),
                Command.create({'product_id': self.product_y.id, 'product_uom_qty': 10}),
            ],
        })
        order.action_confirm()
        self.env['sale.order.line'].flush_recordset()

        # Test public read_group API
        grouped_data = self.SaleReport.sudo().read_group(
            domain=[('order_reference', '=', f'sale.order,{order.id}')],
            groupby=['brand_id'],
            aggregates=['product_uom_qty:sum'],
        )
        brand_groups = dict(grouped_data)

        self.assertIn(self.brand_x.id, brand_groups)
        self.assertEqual(brand_groups[self.brand_x.id], 5.0)
        self.assertIn(self.brand_y.id, brand_groups)
        self.assertEqual(brand_groups[self.brand_y.id], 10.0)

        # Test internal _read_group API returning model records
        grouped_records = self.SaleReport.sudo()._read_group(
            domain=[('order_reference', '=', f'sale.order,{order.id}')],
            groupby=['brand_id'],
            aggregates=['product_uom_qty:sum'],
        )
        record_groups = {brand: qty for brand, qty in grouped_records}
        self.assertIn(self.brand_x, record_groups)
        self.assertEqual(record_groups[self.brand_x], 5.0)
        self.assertIn(self.brand_y, record_groups)
        self.assertEqual(record_groups[self.brand_y], 10.0)

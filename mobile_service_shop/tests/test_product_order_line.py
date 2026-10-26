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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import timedelta
from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductOrderLine(TransactionCase):
    """Test suite for product.order.line model (product_order_line.py)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({'name': 'Order Line Customer'})
        cls.brand = cls.env['mobile.brand'].create({'brand_name': 'Nokia'})
        cls.model = cls.env['brand.model'].create({
            'mobile_brand_name': cls.brand.id,
            'mobile_brand_models': 'G42 5G',
        })
        cls.service = cls.env['mobile.service'].create({
            'person_name': cls.customer.id,
            'brand_name': cls.brand.id,
            'model_name': cls.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
        })

        cls.part_tmpl = cls.env['product.template'].create({
            'name': 'Charging Board',
            'is_a_parts': True,
            'list_price': 22.0,
        })
        cls.part_product = cls.part_tmpl.product_variant_id

    def test_01_onchange_product_id(self):
        """Test onchange sets price_unit and product_uom correctly."""
        line = self.env['product.order.line'].new({
            'product_order_id': self.service.id,
            'product_id': self.part_product.id,
        })
        line._onchange_product_id()
        self.assertEqual(line.price_unit, 22.0)
        self.assertEqual(line.product_uom, self.part_product.uom_id.name)

    def test_02_compute_part_price(self):
        """Test computation of part_price as price_unit * product_uom_qty."""
        line = self.env['product.order.line'].create({
            'product_order_id': self.service.id,
            'product_id': self.part_product.id,
            'product_uom': 'Units',
            'price_unit': 25.0,
            'product_uom_qty': 4.0,
        })
        self.assertEqual(line.part_price, 100.0)

    def test_03_recompute_on_field_changes(self):
        """Test that modifying price_unit or product_uom_qty dynamically updates part_price."""
        line = self.env['product.order.line'].create({
            'product_order_id': self.service.id,
            'product_id': self.part_product.id,
            'product_uom': 'Units',
            'price_unit': 20.0,
            'product_uom_qty': 2.0,
        })
        self.assertEqual(line.part_price, 40.0)

        line.write({'price_unit': 30.0})
        self.assertEqual(line.part_price, 60.0)

        line.write({'product_uom_qty': 3.0})
        self.assertEqual(line.part_price, 90.0)

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

from odoo import Command
from odoo.tests import TransactionCase


class ProductWiseShippingCommon(TransactionCase):
    """Shared fixtures for the Product Wise Shipping Method tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'PWSM Test Customer',
        })

        # Two shipping methods, each with its own (service) delivery product.
        cls.ship_product_a = cls._create_delivery_product(
            'PWSM Shipping A', 10.0)
        cls.ship_product_b = cls._create_delivery_product(
            'PWSM Shipping B', 25.0)
        cls.carrier_a = cls._create_carrier(
            'PWSM Carrier A', cls.ship_product_a)
        cls.carrier_b = cls._create_carrier(
            'PWSM Carrier B', cls.ship_product_b)

        ProductTemplate = cls.env['product.template']
        # Products that carry a shipping method.
        cls.product_a1 = ProductTemplate.create({
            'name': 'PWSM Product A1', 'type': 'consu', 'list_price': 100.0,
            'shipping_method_id': cls.carrier_a.id,
        })
        cls.product_a2 = ProductTemplate.create({
            'name': 'PWSM Product A2', 'type': 'consu', 'list_price': 150.0,
            'shipping_method_id': cls.carrier_a.id,
        })
        cls.product_b1 = ProductTemplate.create({
            'name': 'PWSM Product B1', 'type': 'consu', 'list_price': 200.0,
            'shipping_method_id': cls.carrier_b.id,
        })
        # Product without any shipping method.
        cls.product_plain = ProductTemplate.create({
            'name': 'PWSM Plain Product', 'type': 'consu', 'list_price': 50.0,
        })

    @classmethod
    def _create_delivery_product(cls, name, price):
        return cls.env['product.product'].create({
            'name': name,
            'type': 'service',
            'list_price': price,
            'sale_ok': True,
        })

    @classmethod
    def _create_carrier(cls, name, product):
        return cls.env['delivery.carrier'].create({
            'name': name,
            'delivery_type': 'fixed',
            'fixed_price': 10.0,
            'product_id': product.id,
        })

    def _create_order(self, templates, qty=1.0, **extra):
        """Create a draft sale order with one line per product template.

        Each template must be different, otherwise the module itself merges
        the lines on create.
        """
        vals = {
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': tmpl.product_variant_id.id,
                    'product_uom_qty': qty,
                }) for tmpl in templates
            ],
        }
        vals.update(extra)
        return self.env['sale.order'].create(vals)

    @staticmethod
    def _lines_for(order, product):
        return order.order_line.filtered(lambda l: l.product_id == product)
